import os
import json
import uuid
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import openai
import google.generativeai as genai
import requests


class DialogueChatbotEmbedder:
    def __init__(self, qdrant_url="http://localhost:6333", model_name='all-MiniLM-L6-v2'):
        """
        Khởi tạo với Qdrant client và sentence transformer model
        """
        self.model = SentenceTransformer(model_name)
        self.client = QdrantClient(url=qdrant_url)
        self.vector_size = self.model.get_sentence_embedding_dimension()
        self.collection_name = "medical_dialogues"

        print(f"Đã khởi tạo model: {model_name}")
        print(f"Vector dimension: {self.vector_size}")

    def create_collection(self, collection_name="medical_dialogues"):
        """Tạo collection trong Qdrant"""
        try:
            # Xóa collection cũ nếu tồn tại (optional)
            try:
                self.client.delete_collection(collection_name)
                print(f"Đã xóa collection cũ: {collection_name}")
            except:
                pass

            # Tạo collection mới
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            print(f"Đã tạo collection: {collection_name}")
            self.collection_name = collection_name

        except Exception as e:
            print(f"Lỗi tạo collection: {e}")

    def prepare_dialogue_data(self, dialogue: Dict[str, str], dialogue_id: int = None) -> List[Dict]:
        """
        Chuẩn bị dữ liệu dialogue để lưu vào Qdrant
        """
        user_text = dialogue.get('user', '').strip()
        assistant_text = dialogue.get('assistant', '').strip()

        if not user_text or not assistant_text:
            return []

        user_embedding = self.model.encode(user_text).tolist()
        assistant_embedding = self.model.encode(assistant_text).tolist()

        combined_text = f"Question: {user_text}\nAnswer: {assistant_text}"
        combined_embedding = self.model.encode(combined_text).tolist()

        points = [
            {
                "id": str(uuid.uuid4()),
                "vector": user_embedding,
                "payload": {
                    "type": "user_question",
                    "dialogue_id": dialogue_id,
                    "text": user_text,
                    "user_text": user_text,
                    "assistant_text": assistant_text,
                    "full_dialogue": combined_text
                }
            },
            {
                "id": str(uuid.uuid4()),
                "vector": combined_embedding,
                "payload": {
                    "type": "full_dialogue",
                    "dialogue_id": dialogue_id,
                    "text": combined_text,
                    "user_text": user_text,
                    "assistant_text": assistant_text,
                    "full_dialogue": combined_text
                }
            }
        ]

        return points

    def insert_dialogue(self, dialogue: Dict[str, str], dialogue_id: int = None):
        """Insert một dialogue vào Qdrant"""
        points = self.prepare_dialogue_data(dialogue, dialogue_id)

        if not points:
            print("Không có dữ liệu hợp lệ để insert")
            return False

        try:
            qdrant_points = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point["payload"]
                ) for point in points
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points
            )

            print(f"Đã insert dialogue ID: {dialogue_id or 'auto'}")
            return True

        except Exception as e:
            print(f"Lỗi insert dialogue: {e}")
            return False

    def process_dialogue_file(self, file_path: str):
        """Xử lý file chứa các đoạn hội thoại"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.jsonl'):
                    dialogues = [json.loads(line.strip()) for line in f if line.strip()]
                else:
                    data = json.load(f)
                    if isinstance(data, dict):
                        dialogues = [data]
                    elif isinstance(data, list):
                        dialogues = data
                    else:
                        raise ValueError("Format file không được hỗ trợ")

            print(f"Đã tải {len(dialogues)} dialogues từ file")

            success_count = 0
            for i, dialogue in enumerate(dialogues):
                if self.insert_dialogue(dialogue, dialogue_id=i + 1):
                    success_count += 1

                if (i + 1) % 10 == 0:
                    print(f"Đã xử lý {i + 1}/{len(dialogues)} dialogues")

            print(f"Hoàn thành! Đã insert thành công {success_count}/{len(dialogues)} dialogues")

        except Exception as e:
            print(f"Lỗi xử lý file: {e}")

    def search_similar_dialogues(self, user_query: str, limit: int = 3) -> List[Dict]:
        """
        Tìm kiếm các dialogue tương tự để làm context
        """
        try:
            query_embedding = self.model.encode(user_query).tolist()

            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter={
                    "must": [
                        {
                            "key": "type",
                            "match": {
                                "value": "user_question"
                            }
                        }
                    ]
                },
                limit=limit,
                with_payload=True
            )

            results = []
            for result in search_results:
                results.append({
                    "score": result.score,
                    "dialogue_id": result.payload.get("dialogue_id"),
                    "user_question": result.payload.get("user_text"),
                    "assistant_response": result.payload.get("assistant_text"),
                    "similarity": result.score
                })

            return results

        except Exception as e:
            print(f"Lỗi tìm kiếm: {e}")
            return []

    def construct_context_prompt(self, user_query: str, similar_dialogues: List[Dict]) -> str:
        """
        Tạo prompt có context từ các dialogue tương tự
        """
        context = ""
        if similar_dialogues:
            context = "Dựa vào các cuộc hội thoại tương tự sau đây:\n\n"
            for i, dialogue in enumerate(similar_dialogues[:3], 1):
                context += f"Ví dụ {i}:\n"
                context += f"Người dùng: {dialogue['user_question']}\n"
                context += f"Trợ lý: {dialogue['assistant_response']}\n"
                context += f"(Độ tương tự: {dialogue['similarity']:.3f})\n\n"

        prompt = f"""Bạn là một trợ lý AI thông minh và hữu ích. 

{context}Hãy trả lời câu hỏi sau của người dùng một cách tự nhiên, chính xác và hữu ích:

Người dùng: {user_query}

Trợ lý:"""

        return prompt


class ChatbotService:
    def __init__(self):
        self.embedder = DialogueChatbotEmbedder()
        # Tên model deepseek bạn muốn (ví dụ ‘deepseek-coder’ hoặc ‘deepseek-llm’)
        self.ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")  # Ollama mặc định là 11434
        try:
            print("ChatbotService đã được khởi tạo thành công")
        except Exception as e:
            print(f"Lỗi khởi tạo ChatbotService: {e}")

    def get_response(self, user_message: str):
        try:
            # 1. Tìm kiếm các dialogue tương tự (bỏ async)
            similar_dialogues = self.embedder.search_similar_dialogues(user_message, limit=3)

            # 2. Tạo prompt bối cảnh
            context = ''
            if similar_dialogues:
                context = '\n'.join([
                    f"Q: {d['user_question']}\nA: {d['assistant_response']}" for d in similar_dialogues
                ])

            prompt = f"Nội dung hội thoại trước:\n{context}\nNgười dùng: {user_message}\nTrả lời:"

            # 3. Gọi LLM (OpenAI)
            response = self.call_llm(prompt)

            # 4. Lưu hội thoại mới (optional, an toàn khi chạy async nhất quán)
            self.save_new_dialogue(user_message, response)

            return {
                "role": "assistant",
                "content": response,
                "context_used": bool(similar_dialogues),
                "similar_count": len(similar_dialogues)
            }

        except Exception as e:
            print(f"Lỗi xử lý tin nhắn: {e}")
            return {
                "role": "assistant",
                "content": "Xin lỗi, tôi gặp lỗi khi xử lý tin nhắn của bạn. Vui lòng thử lại.",
                "error": True
            }

    def call_llm(self, prompt: str) -> str:
        try:
            url = f"{self.ollama_url}/v1/chat/completions"
            payload = {
                "model": self.ollama_model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            }
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Xử lý response: Ollama trả về ở data['choices'][0]['message']['content']
            content = data["choices"][0]["message"]["content"].strip()
            return content
        except Exception as e:
            print(f"Lỗi gọi Deepseek Ollama: {e}")
            return "Xin lỗi, tôi gặp lỗi khi tạo phản hồi từ Deepseek qua Ollama."

    def save_new_dialogue(self, user_message: str, assistant_response: str):
        try:
            dialogue = {
                "user": user_message,
                "assistant": assistant_response
            }
            self.embedder.insert_dialogue(dialogue)
        except Exception as e:
            print(f"Lỗi lưu dialogue: {e}")


# Khởi tạo các instance
embedder = DialogueChatbotEmbedder(
    qdrant_url="http://localhost:6333",
    model_name='all-MiniLM-L6-v2'
)
chatbot_service = ChatbotService()
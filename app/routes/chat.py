from flask import Response, request, jsonify
from flask_restx import Resource, Namespace
from app.services.chat import chat_bot
from app.core.Qdrant_chatbot import chatbot_service

chat_namespace = Namespace("chat", description="Chat Bot")


@chat_namespace.route("/chatbot")
class ChatBot(Resource):
    def post(self):
        """Send a message and receive a chat response with context enhancement."""
        try:
            data = request.get_json()
            print(f"Received data: {data}")

            # Validate input
            if not data or 'message' not in data:
                return {'error': 'Message is required'}, 400

            user_message = data.get("message", "").strip()
            if not user_message:
                return {'error': 'Message cannot be empty'}, 400

            # Get response from chatbot service
            response = chatbot_service.get_response(user_message)

            # Ensure response is a dict (not a Response object)
            if isinstance(response, dict):
                return response, 200
            else:
                # Fallback if response is not a dict
                return {
                    'role': 'assistant',
                    'content': str(response),
                    'context_used': False,
                    'similar_count': 0
                }, 200

        except Exception as e:
            print(f"API Error: {str(e)}")
            return {
                'role': 'assistant',
                'content': f'Xin lỗi, đã xảy ra lỗi: {str(e)}',
                'error': True
            }, 500
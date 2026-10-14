import httpx
from typing import Optional, Dict, Any
from core.config import settings
from core.logging import logger


class ChatwootClient:
    def __init__(self):
        self.base_url = settings.CHATWOOT_API_URL
        self.token = settings.CHATWOOT_API_ACCESS_TOKEN
        self.account_id = settings.CHATWOOT_ACCOUNT_ID
        self.inbox_id = settings.CHATWOOT_INBOX_ID

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "api_access_token": self.token or "",
            "Content-Type": "application/json",
        }

    async def get_or_create_contact(self, phone_number: str, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Busca o crea un contacto en Chatwoot por número telefónico."""
        if not self.token:
            return None
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/search"
        async with httpx.AsyncClient(timeout=settings.HTTP_CLIENT_TIMEOUT) as client:
            try:
                res = await client.get(url, params={"q": phone_number}, headers=self.headers)
                if res.status_code == 200:
                    payload = res.json().get("payload", [])
                    if payload:
                        return payload[0]

                # Crear si no existe
                create_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts"
                create_res = await client.post(
                    create_url,
                    json={"phone_number": phone_number, "name": name or phone_number},
                    headers=self.headers
                )
                if create_res.status_code in (200, 201):
                    return create_res.json().get("payload", {}).get("contact")
            except Exception as e:
                logger.error(f"[CHATWOOT_CLIENT] Error al buscar/crear contacto {phone_number}: {e}")
        return None

    async def get_or_create_conversation(self, contact_id: int) -> Optional[int]:
        """Obtiene la conversación activa para un contacto o crea una nueva en el inbox oficial."""
        if not self.token:
            return None
        # 1. Buscar conversaciones activas del contacto
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/contacts/{contact_id}/conversations"
        async with httpx.AsyncClient(timeout=settings.HTTP_CLIENT_TIMEOUT) as client:
            try:
                res = await client.get(url, headers=self.headers)
                if res.status_code == 200:
                    payload = res.json().get("payload", [])
                    if payload:
                        # Retornar la primera conversación abierta o reciente
                        return payload[0].get("id")

                # 2. Si no tiene conversación abierta, crear una nueva
                create_url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations"
                create_res = await client.post(
                    create_url,
                    json={
                        "contact_id": contact_id,
                        "inbox_id": self.inbox_id,
                        "status": "open",
                    },
                    headers=self.headers
                )
                if create_res.status_code in (200, 201):
                    return create_res.json().get("id")
            except Exception as e:
                logger.error(f"[CHATWOOT_CLIENT] Error al obtener/crear conversación para contacto {contact_id}: {e}")
        return None

    async def send_message(self, conversation_id: int, content: str, is_private: bool = False, message_type: str = "outgoing") -> bool:
        """Envía un mensaje saliente, entrante o nota interna a una conversación en Chatwoot."""
        if not self.token:
            return False
        url = f"{self.base_url}/api/v1/accounts/{self.account_id}/conversations/{conversation_id}/messages"
        async with httpx.AsyncClient(timeout=settings.HTTP_CLIENT_TIMEOUT) as client:
            try:
                payload = {
                    "content": content,
                    "private": is_private,
                }
                if message_type == "incoming":
                    payload["message_type"] = "incoming"

                res = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                return res.status_code in (200, 201)
            except Exception as e:
                logger.error(f"[CHATWOOT_CLIENT] Error al enviar mensaje a conv #{conversation_id}: {e}")
                return False

    async def create_private_note(self, conversation_id: int, note_text: str) -> bool:
        """Agrega una nota interna privada (ej. detalles de ticket) visible solo para operadores."""
        return await self.send_message(conversation_id, note_text, is_private=True)


chatwoot_client = ChatwootClient()

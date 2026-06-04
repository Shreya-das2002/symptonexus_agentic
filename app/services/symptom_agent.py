# import json
# from typing import Any

# import requests
# from sqlalchemy.orm import Session

# from app.config import settings
# from app.prompts.system_prompt import SYSTEM_PROMPT
# from app.services.doctor_service import DoctorService


# class SymptomAgent:
#     def __init__(self, db: Session):
#         self.db = db
#         self.doctor_service = DoctorService(db)
#         self.base_url = settings.ollama_base_url.rstrip("/")
#         self.model = settings.ollama_model
#         self.timeout = settings.ollama_timeout

#     def _tools_schema(self) -> list[dict[str, Any]]:
#         return [
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "get_specializations",
#                     "description": "Get all supported doctor specializations from the platform database.",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {},
#                     },
#                 },
#             },
#             {
#                 "type": "function",
#                 "function": {
#                     "name": "search_doctors",
#                     "description": "Search doctors from the platform by specialization or keyword.",
#                     "parameters": {
#                         "type": "object",
#                         "properties": {
#                             "specialization": {
#                                 "type": "string",
#                                 "description": "Exact or likely specialization name such as Dermatologist, Cardiologist, Pediatrician, General Physician.",
#                             },
#                             "query": {
#                                 "type": "string",
#                                 "description": "Free-text search, such as skin, diabetes, heart, child fever.",
#                             },
#                             "limit": {
#                                 "type": "integer",
#                                 "description": "Maximum doctors to return.",
#                                 "default": 5,
#                             },
#                         },
#                     },
#                 },
#             },
#         ]

#     def _call_local_llm(
#         self,
#         messages: list[dict[str, Any]],
#         tools: list[dict[str, Any]] | None = None,
#     ) -> dict[str, Any]:
#         payload: dict[str, Any] = {
#             "model": self.model,
#             "messages": messages,
#             "stream": False,
#             "options": {
#                 "temperature": 0.3,
#             },
#         }

#         if tools:
#             payload["tools"] = tools

#         response = requests.post(
#             f"{self.base_url}/api/chat",
#             json=payload,
#             timeout=self.timeout,
#         )
#         response.raise_for_status()
#         return response.json()

#     def _run_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
#         if name == "get_specializations":
#             return {"specializations": self.doctor_service.get_specializations()}

#         if name == "search_doctors":
#             specialization = arguments.get("specialization")
#             query = arguments.get("query")

#             # Important fix:
#             # if specialization is already identified, do not also filter by raw symptom text
#             # because symptom text usually does not exist in doctor profile fields.
#             if specialization:
#                 query = None

#             limit = int(arguments.get("limit", 5))

#             doctors = self.doctor_service.search_doctors(
#                 specialization=specialization,
#                 query=query,
#                 limit=limit,
#             )
#             return {"doctors": doctors}

#         return {"error": f"Unknown tool: {name}"}

#     @staticmethod
#     def _extract_suggested_specialization(
#         reply: str,
#         doctors: list[dict[str, Any]],
#         specializations: list[dict[str, Any]],
#     ) -> str | None:
#         if doctors and doctors[0].get("specialization"):
#             if isinstance(doctors[0]["specialization"], list) and doctors[0]["specialization"]:
#                 return doctors[0]["specialization"][0]

#         known = [item["name"] for item in specializations] if specializations else [
#             "General Physician",
#             "Cardiologist",
#             "Dermatologist",
#             "Pediatrician",
#             "General Surgeon",
#             "Dentist",
#             "Ophthalmologist",
#             "ENT Specialist",
#             "Psychiatrist",
#             "Neurologist",
#             "Orthopedic",
#             "Gynecologist",
#         ]

#         lower_reply = reply.lower()
#         for item in known:
#             if item.lower() in lower_reply:
#                 return item
#         return None

#     def chat(
#         self,
#         user_message: str,
#         conversation: list[dict[str, str]] | None = None,
#     ) -> dict[str, Any]:
#         conversation = conversation or []

#         gathered_specializations = self.doctor_service.get_specializations()
#         gathered_doctors: list[dict[str, Any]] = []

#         specialization_names = ", ".join(
#             [item["name"] for item in gathered_specializations]
#         )

#         system_content = SYSTEM_PROMPT
#         if specialization_names:
#             system_content += (
#                 "\n\nAvailable specializations in database: "
#                 f"{specialization_names}"
#                 "\nUse these exact specialization names when suggesting or searching doctors."
#             )

#         messages: list[dict[str, Any]] = [
#             {"role": "system", "content": system_content}
#         ]

#         for item in conversation[-6:]:
#             messages.append(
#                 {
#                     "role": item["role"],
#                     "content": item["content"],
#                 }
#             )

#         messages.append({"role": "user", "content": user_message})

#         first_pass = self._call_local_llm(
#             messages=messages,
#             tools=self._tools_schema(),
#         )

#         assistant_message = first_pass.get("message", {})
#         tool_calls = assistant_message.get("tool_calls", []) or []

#         messages.append(assistant_message)

#         for call in tool_calls:
#             function = call.get("function", {})
#             tool_name = function.get("name")
#             arguments = function.get("arguments", {})

#             if isinstance(arguments, str):
#                 try:
#                     arguments = json.loads(arguments)
#                 except json.JSONDecodeError:
#                     arguments = {}

#             tool_result = self._run_tool(tool_name, arguments)

#             if "doctors" in tool_result:
#                 gathered_doctors = tool_result["doctors"]

#             if "specializations" in tool_result:
#                 gathered_specializations = tool_result["specializations"]

#             messages.append(
#                 {
#                     "role": "tool",
#                     "content": json.dumps(tool_result, ensure_ascii=False),
#                 }
#             )

#         final_response = self._call_local_llm(messages=messages)
#         reply = final_response.get("message", {}).get(
#             "content",
#             "Sorry, I could not process that right now.",
#         )

#         specialization = self._extract_suggested_specialization(
#             reply=reply,
#             doctors=gathered_doctors,
#             specializations=gathered_specializations,
#         )

#         return {
#             "reply": reply,
#             "suggested_specialization": specialization,
#             "doctors": gathered_doctors,
#             "metadata": {
#                 "model": self.model,
#                 "tool_calls_used": len(tool_calls),
#                 "specializations_loaded": len(gathered_specializations),
#             },
#         }


# import json
# from typing import Any

# import requests
# from sqlalchemy.orm import Session

# from app.config import settings
# from app.prompts.system_prompt import SYSTEM_PROMPT
# from app.services.doctor_service import DoctorService


# class SymptomAgent:
#     def __init__(self, db: Session):
#         self.db = db
#         self.doctor_service = DoctorService(db)
#         self.base_url = settings.ollama_base_url.rstrip("/")
#         self.model = settings.ollama_model
#         self.timeout = settings.ollama_timeout

#     def _call_local_llm(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
#         payload = {
#             "model": self.model,
#             "messages": messages,
#             "stream": False,
#             "format": "json",
#             "options": {
#                 "temperature": 0,
#                 "num_predict": 80
#             },
#         }

#         response = requests.post(
#             f"{self.base_url}/api/chat",
#             json=payload,
#             timeout=self.timeout,
#         )
#         response.raise_for_status()
#         return response.json()

#     def _build_reply(self, specialization: str | None, doctors: list[dict[str, Any]]) -> str:
#         if doctors:
#             names = ", ".join([d["full_name"] for d in doctors[:3]])
#             return (
#                 f"Based on your symptoms, you should consult a {specialization}. "
#                 f"Available doctor(s): {names}. You may proceed with booking."
#             )

#         if specialization:
#             return (
#                 f"Based on your symptoms, you should consult a {specialization}. "
#                 f"No active doctor is available in this category right now."
#             )

#         return "I could not identify the correct specialist from your symptoms. Please describe your symptoms more clearly."

#     def chat(
#         self,
#         user_message: str,
#         conversation: list[dict[str, str]] | None = None,
#     ) -> dict[str, Any]:
#         conversation = conversation or []

#         specializations = self.doctor_service.get_specializations()
#         specialization_names = [s["name"] for s in specializations]

#         system_content = (
#             SYSTEM_PROMPT
#             + "\n\nYou are a symptom-to-doctor-specialization classifier."
#             + "\nChoose exactly one specialization from this list:"
#             + "\n" + ", ".join(specialization_names)
#             + "\n\nReturn ONLY valid JSON in this format:"
#             + '\n{"specialization": "Dermatologist", "reason": "skin rash and itching"}'
#             + "\n\nRules:"
#             + "\n- skin, rash, itching, allergy -> Dermatologist"
#             + "\n- sugar, diabetes, high glucose -> General Physician"
#             + "\n- child, baby, kid -> Pediatrician"
#             + "\n- eye, vision -> Ophthalmologist"
#             + "\n- ear, nose, throat -> ENT Specialist"
#             + "\n- anxiety, depression, sleep problem -> Psychiatrist"
#             + "\n- chest pain, heart -> Cardiologist"
#         )

        # messages = [
        #     {"role": "system", "content": system_content},
        # ]

        # for item in conversation[-4:]:
        #     messages.append({"role": item["role"], "content": item["content"]})

        # messages.append({"role": "user", "content": user_message})

        # llm_response = self._call_local_llm(messages)
        # content = llm_response.get("message", {}).get("content", "{}")

        # specialization = None
        # reason = None

        # try:
        #     parsed = json.loads(content)
        #     specialization = parsed.get("specialization")
        #     reason = parsed.get("reason")
        # except Exception:
        #     specialization = None

        # if specialization not in specialization_names:
        #     specialization = None

        # doctors = []
        # if specialization:
        #     doctors = self.doctor_service.search_doctors(
        #         specialization=specialization,
        #         query=None,
        #         limit=5,
        #     )

        # reply = self._build_reply(specialization, doctors)

        # return {
        #     "reply": reply,
        #     "suggested_specialization": specialization,
        #     "doctors": doctors,
        #     "metadata": {
        #         "model": self.model,
        #         "mode": "fast_json_llm_decision",
        #         "reason": reason,
        #         "specializations_loaded": len(specializations),
        #     },
        # }
        
        
import json
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.services.doctor_service import DoctorService


class SymptomAgent:
    def __init__(self, db: Session):
        self.db = db
        self.doctor_service = DoctorService(db)
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout

    def is_greeting(self, message: str) -> bool:
        msg = message.lower().strip()
        greetings = [
            "hi",
            "hii",
            "hello",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
            "namaste",
        ]
        return any(msg == g or msg.startswith(g + " ") for g in greetings)

    def is_empty_or_invalid(self, message: str) -> bool:
        return not message or not message.strip()

    def _call_local_llm(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_predict": 80,
            },
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _build_reply(
        self,
        specialization: str | None,
        doctors: list[dict[str, Any]],
    ) -> str:
        if doctors:
            names = ", ".join([doc["full_name"] for doc in doctors[:3]])
            return (
                f"Based on your symptoms, you should consult a {specialization}. "
                f"Available doctor(s): {names}. You may proceed with booking."
            )

        if specialization:
            return (
                f"Based on your symptoms, you should consult a {specialization}. "
                f"No active doctor is available in this category right now."
            )

        return (
            "Hello! Please describe your symptoms, and I will suggest the right "
            "doctor category for booking."
        )

    def chat(
        self,
        user_message: str,
        conversation: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        conversation = conversation or []

        if self.is_empty_or_invalid(user_message):
            return {
                "reply": "Please describe your symptoms so I can suggest the right doctor.",
                "suggested_specialization": None,
                "doctors": [],
                "metadata": {
                    "model": self.model,
                    "mode": "empty_message",
                },
            }

        if self.is_greeting(user_message):
            return {
                "reply": "Hello! Please describe your symptoms, and I will suggest the right doctor for you.",
                "suggested_specialization": None,
                "doctors": [],
                "metadata": {
                    "model": self.model,
                    "mode": "greeting",
                },
            }

        specializations = self.doctor_service.get_specializations()
        specialization_names = [item["name"] for item in specializations]

        system_content = (
            SYSTEM_PROMPT
            + "\n\nYou are a symptom-to-doctor-specialization classifier."
            + "\nChoose exactly one specialization from this list only when the user clearly describes a medical symptom:"
            + "\n"
            + ", ".join(specialization_names)
            + "\n\nIf the user is greeting, casual chat, booking question, or not describing symptoms, return null."
            + "\n\nReturn ONLY valid JSON in this format:"
            + '\n{"specialization": "Dermatologist", "reason": "skin rash and itching"}'
            + '\n{"specialization": null, "reason": "no medical symptom found"}'
            + "\n\nRules:"
            + "\n- hi, hello, hey, good morning -> null"
            + "\n- skin, rash, itching, allergy, redness, pimples -> Dermatologist"
            + "\n- sugar, diabetes, high glucose, weakness, fever, cough, cold -> General Physician"
            + "\n- child, baby, kid, newborn -> Pediatrician"
            + "\n- eye, vision, blurred vision, eye redness -> Ophthalmologist"
            + "\n- ear, nose, throat, sinus -> ENT Specialist"
            + "\n- anxiety, depression, stress, sleep problem -> Psychiatrist"
            + "\n- chest pain, heart, palpitations, high bp -> Cardiologist"
            + "\n- joint pain, bone pain, fracture, back pain, knee pain -> Orthopedic"
            + "\n- pregnancy, periods, PCOS, uterus -> Gynecologist"
            + "\n- tooth pain, teeth, gum, cavity -> Dentist"
            + "\n- severe headache, migraine, numbness, nerve issue -> Neurologist"
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_content}
        ]

        for item in conversation[-4:]:
            messages.append(
                {
                    "role": item["role"],
                    "content": item["content"],
                }
            )

        messages.append({"role": "user", "content": user_message})

        llm_response = self._call_local_llm(messages)
        content = llm_response.get("message", {}).get("content", "{}")

        specialization = None
        reason = None

        try:
            parsed = json.loads(content)
            specialization = parsed.get("specialization")
            reason = parsed.get("reason")
        except Exception:
            specialization = None
            reason = "invalid json response from model"

        if specialization not in specialization_names:
            specialization = None

        doctors: list[dict[str, Any]] = []

        if specialization:
            doctors = self.doctor_service.search_doctors(
                specialization=specialization,
                query=None,
                limit=5,
            )

        reply = self._build_reply(
            specialization=specialization,
            doctors=doctors,
        )

        return {
            "reply": reply,
            "suggested_specialization": specialization,
            "doctors": doctors,
            "metadata": {
                "model": self.model,
                "mode": "fast_json_llm_decision",
                "reason": reason,
                "specializations_loaded": len(specializations),
            },
        }
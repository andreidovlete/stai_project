import json
import re
import random
import os
import requests
from collections import deque
import spacy
from thefuzz import fuzz
from sentence_transformers import SentenceTransformer, util


class ChatBot:
    def __init__(self, intents_path="intents.json", memory_size=5):
        intents_abs_path = os.path.join(os.path.dirname(__file__), intents_path)
        with open(intents_abs_path, "r", encoding="utf-8") as f:
            self.intents = json.load(f)["intents"]
        self.context = deque(maxlen=memory_size)
        self.user_memory = {}
        self.previous_intent = None
        self.nlp = spacy.load("en_core_web_sm")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.serpapi_key = "APIKEY"

    def _normalize(self, text):
        return re.sub(r'[^\w\s]', '', text.lower())

    def classify_intent(self, message):
        message_norm = self._normalize(message)
        best_intent = None
        best_score = 0

        # Fuzzy matching
        for intent in self.intents:
            for pattern in intent["patterns"]:
                pattern_norm = self._normalize(pattern)
                score = fuzz.partial_ratio(message_norm, pattern_norm) if len(pattern_norm) >= 4 else 0
                if score > best_score:
                    best_score = score
                    best_intent = intent

        if best_score > 90:
            return best_intent

        # Semantic similarity
        best_sim = 0
        best_intent_semantic = None
        message_emb = self.model.encode(message, convert_to_tensor=True)

        for intent in self.intents:
            for pattern in intent["patterns"]:
                pattern_emb = self.model.encode(pattern, convert_to_tensor=True)
                sim = util.cos_sim(message_emb, pattern_emb).item()
                if sim > best_sim:
                    best_sim = sim
                    best_intent_semantic = intent

        if best_sim > 0.7:
            return best_intent_semantic

        return None

    def _get_fallback_response(self, query):
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "engine": "google"
            }
            response = requests.get(url, params=params)
            data = response.json()

            if "answer_box" in data and "answer" in data["answer_box"]:
                return data["answer_box"]["answer"]
            elif "organic_results" in data and data["organic_results"]:
                return data["organic_results"][0].get("snippet", "Here's what I found.")
            else:
                return "I searched online but couldn't find a clear answer 😕"
        except Exception:
            return "Something went wrong while searching online."

    def _extract_entities(self, message):
        doc = self.nlp(message)
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                self.user_memory["name"] = ent.text
            elif ent.label_ == "DATE":
                self.user_memory["birthday"] = ent.text

        patterns = [
            r"\bmy name is (\w+)",
            r"\bi(?:'m| am) (\w+)",
            r"\bthis is (\w+)",
            r"\bit(?:'s| is) (\w+)",
            r"\bthey call me (\w+)",
            r"\bthe name'?s (\w+)",
            r"\bname[:\-]?\s*(\w+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                self.user_memory["name"] = match.group(1)
                break

    def _contextual_response(self, message, current_intent):
        msg = message.lower().strip()
        if self.previous_intent:
            prev_intent = next((i for i in self.intents if i["tag"] == self.previous_intent), None)
            if prev_intent and "followups" in prev_intent:
                for key_phrase, responses in prev_intent["followups"].items():
                    if key_phrase in msg:
                        return random.choice(responses)
        return None

    def get_response(self, message):
        self.context.append(message)
        self._extract_entities(message)
        current_intent = self.classify_intent(message)

        # If user says their name
        if "name" in self.user_memory and any(re.search(p, message, re.IGNORECASE) for p in [
            r"\bmy name is (\w+)",
            r"\bi(?:'m| am) (\w+)",
            r"\bthis is (\w+)",
            r"\bit(?:'s| is) (\w+)",
            r"\bthey call me (\w+)",
            r"\bthe name'?s (\w+)",
            r"\bname[:\-]?\s*(\w+)"
        ]):
            return f"Nice to meet you, {self.user_memory['name']}! 😊"

        if current_intent:
            tag = current_intent["tag"]

            if tag == "ask_name":
                if "name" in self.user_memory:
                    return random.choice([
                        f"I think your name is {self.user_memory['name']}.",
                        f"You're {self.user_memory['name']}, right?",
                        f"You told me you're {self.user_memory['name']}. Is that still correct?"
                    ])
                else:
                    return "Hmm, I don’t know your name yet. What should I call you?"

            contextual = self._contextual_response(message, current_intent)
            response = contextual if contextual else random.choice(current_intent["responses"])

            if "{name}" in response and "name" in self.user_memory:
                response = response.replace("{name}", self.user_memory["name"])

            self.previous_intent = tag
            return response

        return self._get_fallback_response(message)

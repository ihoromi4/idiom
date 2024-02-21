from typing import Any
import multiprocessing

import numpy as np
from transformers import AutoProcessor, BarkModel


class AudioNarator:
    def __init__(self):
        self.voice_preset = "v2/en_speaker_6"

        self.device = "cuda:1"
        self.processor = AutoProcessor.from_pretrained("suno/bark-small", device=self.device)
        self.model = BarkModel.from_pretrained("suno/bark-small").to(device=self.device)

        self.sample_rate = self.model.generation_config.sample_rate

    def generate_audio(self, text: str) -> np.ndarray:
        inputs = self.processor(text, voice_preset=self.voice_preset).to(device=self.device)
    
        audio_array = self.model.generate(**inputs)
        audio_array = audio_array.cpu().numpy().squeeze()

        return audio_array
    

class MultiprocessingAudioNarator:
    def __init__(self):
        self.todo = multiprocessing.Queue()
        self.results = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=self.vocalisation_loop, args=(self.todo, self.results))
        self.process.daemon = True
        self.start()

    def start(self):
        self.process.start()

    def generate_audio(self, text: str, wiat: bool = True) -> np.ndarray:
        self.todo.put(dict(text=text))
        return self.results.get()["data"]
    
    def request(self, text: str):
        self.todo.put(dict(text=text))

    def is_available(self):
        return not self.results.empty()
    
    def is_busy(self):
        return not self.todo.empty()
    
    def get(self) -> dict[str, Any]:
        return self.results.get()

    def vocalisation_loop(self, todo, results):
        voice_preset = "v2/en_speaker_9"
        device = "cuda:1"

        processor = AutoProcessor.from_pretrained("suno/bark-small", device=device)
        model = BarkModel.from_pretrained("suno/bark-small").to(device=device)

        while True:
            message = todo.get()
            text = message["text"]

            inputs = processor(text, voice_preset=voice_preset).to(device=device)
        
            audio_array = model.generate(**inputs)
            audio_array = audio_array.cpu().numpy().squeeze()

            results.put(dict(text=text, data=audio_array))

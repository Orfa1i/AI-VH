import torch
from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

MODEL_PATH = "./model"

print("Configuring 4-bit quantization for RTX 4060...")
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
)

print("Loading processor and model...")
processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH,
    quantization_config=bnb_config,
    device_map="auto",
)
print("Model loaded successfully onto GPU!")

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What are the classic symptoms of type 2 diabetes?"}
        ],
    }
]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
).to("cuda")

print("Generating response...")
with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=250, do_sample=False)

result = processor.decode(output[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
print("\n--- MedGemma response ---")
print(result)


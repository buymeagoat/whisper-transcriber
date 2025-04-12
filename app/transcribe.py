import argparse
import whisper
import json
import os


def transcribe_audio(input_path, model_size="base", language=None, output_path=None):
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Audio file not found: {input_path}")

    print(f"Loading Whisper model: {model_size}...")
    model = whisper.load_model(model_size)

    print("Transcribing audio...")
    result = model.transcribe(input_path, language=language)

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Transcription saved to {output_path}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    return result


def main():
    parser = argparse.ArgumentParser(description="Transcribe an audio file using OpenAI Whisper")
    parser.add_argument("--input", required=True, help="Path to the input audio file")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--language", help="Optional language override (e.g., 'en')")
    parser.add_argument("--output", help="Optional path to save JSON transcription result")

    args = parser.parse_args()
    transcribe_audio(args.input, args.model, args.language, args.output)


if __name__ == "__main__":
    main()

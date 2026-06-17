# Necessary Dependencies
# --------------------------------------------------------------------------------
# Custom
from app.startup.init import *
# AI
import easyocr
from llama_cpp import Llama

# AI Translation Module
# ================================================================================

def translation_server(input_queue, output_queue, stop_event, translation_model_path, gpu_available, lang_code, native_lang, max_tokens):

    print("(Re)loading text translation model...")
    # Load Translation Model
    try:
        if gpu_available:
            translation_model = Llama(model_path=translation_model_path, verbose=False, n_gpu_layers=-1)
        else:
            translation_model = Llama(model_path=translation_model_path, verbose=False, n_gpu_layers=0)
    except Exception as e:
        # Abort program if model is not available online or offline
        print("Transformer text translation model not present!")
        print("ERROR: " + str(e))
        abort_program()

    print("(Re)loading OCR reader...")
    # Load chosen EasyOCR reader
    global easy_reader
    match lang_code:
        case 0:
            print("Preparing EasyOCR latin dictionary...")
            easy_reader = easyocr.Reader(['en', 'fr', 'de', 'es', 'it'])
        case 1:
            print("Preparing EasyOCR cyrillic dictionary...")
            easy_reader = easyocr.Reader(["ru", "rs_cyrillic", "be", "bg", "uk", "mn", "en"])
        case 2:
            print("Preparing EasyOCR arabic dictionary...")
            easy_reader = easyocr.Reader(['ar', 'fa', 'ur', 'en'])
        case 3:
            print("Preparing EasyOCR chinese dictionary...")
            easy_reader = easyocr.Reader(['ch_sim', 'en'])
        case 4:
            print("Preparing EasyOCR japanese dictionary...")
            easy_reader = easyocr.Reader(['ja', 'en'])
        case 5:
            print("Preparing EasyOCR korean dictionary...")
            easy_reader = easyocr.Reader(['ko', 'en'])

    print("\n\nTranslEYEtor server ready...\n")

    EMPTY_RESPONSE = ("@EMPTY", [-250, -250], [-250, -250])
    READY_RESPONSE = ("@READY", [-250, -250], [-250, -250])

    output_queue.put(READY_RESPONSE)

    while not stop_event.is_set():

        try:

            # Check for new data input 0.1 second
            try:
                image_url = input_queue.get(timeout=0.1)
            except Exception:
                continue

            start_time = time.time()

            print("EasyOCR /// Captured image. Parsing...")

            # Convert image text to text via EasyOCR
            ocr_output = easy_reader.readtext(image_url, paragraph=True)

            print(f"EasyOCR /// Image parsed in {time.time() - start_time} seconds.")

            if not ocr_output:
                print("EasyOCR /// Image contains no text!")
                output_queue.put(EMPTY_RESPONSE)

            # Pass on answer to translation model
            for text_item in ocr_output:

                source_text = text_item[1]

                print(f"Hy-MT2-1.8B-Q4_K_M /// Translating text chunk to {native_lang}...")
                translation_prompt = f"Translate without explanation to {native_lang}: {source_text}"
                full_response = translation_model(translation_prompt, max_tokens=max_tokens)
                
                # Output -> Text + BBOX coords
                response = full_response["choices"][0]["text"].strip()
                bbox_top_left = text_item[0][0]
                bbox_bottom_right = text_item[0][2]

                # Put output into output_queue
                output_queue.put((response, bbox_top_left, bbox_bottom_right))

            print(f"Finished in {time.time() - start_time} seconds.")

        except Exception as e:
            output_queue.put(EMPTY_RESPONSE)
            print(e)

# ================================================================================
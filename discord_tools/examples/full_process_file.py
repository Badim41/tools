from discord_tools.lalalai import full_process_file_pipeline, LalalAIModes

if __name__ == "__main__":
    input_str = input("Введите имя файла или ссылку на ютуб:\n")
    all_processed_files = full_process_file_pipeline(input_str, wav_always=True, modes=[LalalAIModes.Vocal_and_Instrumental, LalalAIModes.Drums, LalalAIModes.Voice_and_Noise])
    print("All results:", all_processed_files)

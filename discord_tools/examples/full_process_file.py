from discord_tools.lalalai import full_process_file_pipeline

if __name__ == "__main__":
    input_str = input("Введите имя файла или ссылку на ютуб:\n")
    all_processed_files = full_process_file_pipeline(input_str, wav_always=True)
    print("All results:", all_processed_files)

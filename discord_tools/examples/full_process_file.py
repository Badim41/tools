from discord_tools.lalalai import full_process_file_pipeline, LalalAI

lalala = LalalAI()
lalala.go_to_site()

if __name__ == "__main__":
    input_str = input("Введите имя файла или ссылку на ютуб:\n")
    all_processed_files = full_process_file_pipeline(input_str, lalala=lalala)
    print("All results:", all_processed_files)

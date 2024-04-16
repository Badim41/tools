from discord_tools.lalalai import LalalAIModes, process_file_pipeline

file_path = input("file:\n")
result_1, result_2 = process_file_pipeline(large_file_name=file_path,
                                           mode=LalalAIModes.Vocal_and_Instrumental)

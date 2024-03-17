from discord_tools.lalalai import LalalAIModes, process_file_pipeline

mp3_file_path = "file.mp3"
result_1, result_2 = process_file_pipeline(large_file_name=mp3_file_path,
                                           mode=LalalAIModes.Vocal_and_Instrumental)

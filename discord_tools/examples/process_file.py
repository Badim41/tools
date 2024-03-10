from discord_tools.lalalai import LalalAI, LalalAIModes, process_file_pipeline

lalala = LalalAI()
lalala.go_to_site()

mp3_file_path = "file.mp3"
crashed, result_1, result_2 = \
    process_file_pipeline(large_file_name=mp3_file_path,
                          mode=LalalAIModes.Vocal_and_Instrumental,
                          lalala=lalala)
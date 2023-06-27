import json

def get_frame_numbers_from_seq_control_file(filename : str):
    with open(filename) as f_in:
        data = json.load(f_in)
        
    frame_numbers = []
    critical_frame_sub_seq = data["critical_frames"]
    
    for critical_frames in critical_frame_sub_seq:
        frame_numbers.extend(range(critical_frames[0], critical_frames[1], 1))
        
    return frame_numbers
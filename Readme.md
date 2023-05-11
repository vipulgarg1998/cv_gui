# GUI
This project is intended to visualize the intermediate results from a computer vision pipeline. It is able to handle SVO dataset files from ZED camera as well as KITTI dataset. Currently, this is very unstable and need further devlopment to be completely utilised in any computer vision project. 

## Create Images Dataset Using GUI for ZED Camera
This functionality is fully tested and working if the steps are followed in the given sequence only. The following sample takes left and right rectified images from the zed camera and display it in the GUI.

- Run the application
  ```
  python3 -m samples.zed_sample
  ```
- Select the SVO filepath.

  <img src="images/zed-select-dataset-file-marked.png" alt="Employee data" title="Employee Data title">
- Start the Player.

  <img src="images/zed-start-marked.png" alt="Employee data" title="Employee Data title">
- Select the directory in which the images will be saved.

  <img src="images/zed-select-save-folder-marked.png" alt="Employee data" title="Employee Data title">
- Enable the auto recording of the images while playing.

  <img src="images/zed-auto-record-marked.png" alt="Employee data" title="Employee Data title">
- Play the Sequencer. Play button will automatically be toggle to Pause. 

  <img src="images/zed-play-marked.png" alt="Employee data" title="Employee Data title">
- Export the timestamps when the file reached to the end. Pause button will automatically be toggle to Play again

  <img src="images/zed-timestamp-export-marked.png" alt="Employee data" title="Employee Data title">

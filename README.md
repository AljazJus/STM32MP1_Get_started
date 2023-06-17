# STM32MP1_Get_started

This repository aims to assist you in initiating the development of applications for the STM32MP1 board. It was created as a project for the "Vhodno-izhodne naprave" class under the guidance of Professor Robert Rozman. Here, we will discuss the fundamentals of programming in Python for the STM32MP1 platform.

### Requirements

#### Hardwear

There are no specific hardware requirements for your computer; you should be able to run the necessary programs on any device, regardlessof its specifications, as long as you can install them.
To get started, you will need the following items:

- Micro USB cable
- 2x USB C cables (you will only need the second cable if your board isn't updated)
- STM32MP1 board
- USB stick

These items are essential for setting up and working with the STM32MP1 board.

#### Softwear 

To successfully follow these tutorials, you will need a host computer running Linux. I personally used Ubuntu 20.04, but I'm unsure if it will work on other distributions. However, you can give it a try if you'd like.

Please note that these tutorials will focus exclusively on creating Python applications and won't cover Linux applications for the STM32MP1 board. If you intend to develop Linux applications specifically for the STM32MP1 board, you'll need to use Linux (Ubuntu 20.04) on your host PC and install the corresponding SDK. You can find a manual installation guide [here](https://wiki.st.com/stm32mpu/wiki/Getting_started/STM32MP1_boards/STM32MP157x-DK2/Develop_on_Arm®_Cortex®-A7/Install_the_SDK), or you can use STM32CubeIDE, which offers an easier and more streamlined process. Simply create a project for the STM32MP1 board in STM32CubeIDE, and you should receive a prompt to install the SDK. You can also follow this [link](https://wiki.stmicroelectronics.cn/stm32mpu/index.php?title=How_to_install_the_Yocto_Project_SDK_in_STM32CubeIDE&oldid=73864) for further instructions.

To begin, you'll need a means to access the terminal on your board. This can be done manually by connecting the board to the terminal, following the instructions provided [here](https://wiki.st.com/stm32mpu/wiki/Getting_started/STM32MP1_boards/STM32MP157x-DK2/Let%27s_start/Execute_basic_commands). Alternatively, you can connect using STM32CubeIDE.

#### Connect to the terminal

For board connectivity, you'll require two cables: a power cable (USB C) to be connected to the port adjacent to the Ethernet port, and a micro USB cable for terminal connection. Please refer to the provided image for clarification: 
![board](/boarn.png)

Once you have connected your board correctly, you should be able to wake it up by pressing the wake-up button. If the board doesn't turn on, please check the following:

1. Ensure that your power cable is connected properly. Some older laptops may not support power through USB, so they won't be able to provide power to the board. In such cases, you can use a phone charger or an alternative power source.
2. Verify that the SD card is plugged in correctly. The board relies on the SD card for proper operation, so make sure it is securely inserted.
3. Check the two switches located on the back of the board. Refer to the provided image to ensure that both switches are turned on as depicted.

By addressing these potential issues, you should be able to power on your board successfully.
![back_board](/back_board.png)


Now you can connect to the board either through CubeIDE or via the terminal, as explained in the provided link. To connect using CubeIDE, locate and press the button highlighted in the image:

![connec_Button](/icon.png)

Once you've established a connection, you should see a confirmation in the console box of CubeIDE, indicating that you are now connected and can begin using Linux commands on the board.

#### Update the board

Now that you have successfully connected the board, you can verify if it is updated and has all the necessary libraries installed. Open the terminal and type the command `x-linux-ai -v`. If you receive a response such as `X-LINUX-AI version: v3.0.0` or a higher version, it means that you have the required version and can proceed otherwise follow the steps below.

1. To begin, you need to download STM32CubeProgrammer from the following [link](https://www.st.com/en/development-tools/stm32cubeprog.html). I recommend installing it on a Windows PC because, in my experience, I encountered issues with the program detecting my board on Linux and macOS.

2. To update your board, please follow this [link](https://wiki.st.com/stm32mpu/wiki/Getting_started/STM32MP1_boards/STM32MP157x-DK2/Let%27s_start/Populate_the_target_and_boot_the_image). It provides detailed instructions on how to populate the target and boot the image, guiding you through the necessary steps. Please note that based on my experience, loading the new software onto the board took approximately three hours. During this time, it is crucial not to disturb the board, as any interruptions or disturbances could potentially cause errors during the update process. It is recommended to allow the update to complete undisturbed to ensure a successful update.

3. Now that the board has been successfully updated, you can proceed with the next steps. In this phase, we will install some libraries required for working with AI. To install these libraries, I recommend connecting your board to the internet using the Ethernet port. Once connected, please follow this [link](https://wiki.st.com/stm32mpu/wiki/X-LINUX-AI_OpenSTLinux_Expansion_Package).


Congratulations! You can now write any Python program on your board. I have provided a sample program that displays the camera feed on the screen. However, there are also numerous examples available on the board that work with AI. If you wish to explore these examples, you will need to connect a USB webcam to the board. Feel free to experiment with these examples and unleash the full potential of your board.

### Load the program on your board

1. The easiest way I found to load programs onto your board is by using a USB stick. On your operating system, copy the files onto the USB stick, then remove it from your computer and insert it into the board.
2. Next, you need to mount your device. When you plugged in your device, the terminal printed out the name of the device. For example, in my case, it was `sda1`. Your device will likely have a similar name. You can check for all the connected USB sticks by typing `ls /dev/ | grep sd`. This command should display all the USB sticks.
3. Now, you need to mount your USB stick. To do this, type `mount /dev/sda1 /media` (change `sda1` to the name of your drive).
4. You can now copy the files. First, navigate to the directory where you want the files to be stored. For example, `cd /usr/local`. Then, copy the file or directory. To load the example given in these tutorials, use `cp -r /media/Vin ./`. If you want to copy a single file, use `cp /media/yourFile.py ./`.
5. After copying the program, use `umount /dev/sda1` to unmount your USB drive, and then remove it from the board.
6. Now, you can run the copied file on your board. For example, `./Vin/camera_launch.sh`. If you want to run a Python program, use `python3.10 yourPython.py`.

These steps should help you successfully load and run your programs on the board.

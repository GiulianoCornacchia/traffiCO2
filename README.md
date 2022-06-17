


# How Routing Strategies Impact Urban Emissions

Authors: Giuliano Cornacchia, Matteo Böhm, Giovanni Mauro, Mirco Nanni, Dino Pedreschi, and Luca Pappalardo.

#### Abstract

Navigation apps use routing algorithms to suggest the best path to reach a user's desired destination. Although undoubtedly useful, navigation apps' impact on the urban environment (e.g., carbon dioxide emissions and population exposure to pollution) is still largely unclear. In this work, we design a simulation framework to assess the impact of routing algorithms on carbon dioxide emissions within an urban environment. Using APIs from TomTom and OpenStreetMap, we find that settings in which either all vehicles or none of them follow a navigation app's suggestion lead to the worst impact in terms of CO$_2$ emissions. In contrast, when just a portion (around half) of vehicles follow these suggestions, and some degree of randomness is added to the remaining vehicles' paths, we observe a reduction in the overall CO$_2$ emissions over the road network. Our work is a first step towards designing next-generation routing principles that may increase urban well-being while satisfying individual needs. 



## Citing
In this repository you can find the code to replicate the analysis of our work regarding the impact of navigation apps on the urban sustainability.
If you use the code in this repository, please cite our paper:

*Cornacchia, G., Böhm, M., Mauro, G., Nanni, M., Pedreschi, D., & Pappalardo, L. (2022). How Routing Diversification Mitigates Urban Emissions. arXiv preprint arXiv:xxxx.xxxx.*

```
@article{cornacchia2022impact,
  title={On the Impact of Navigation Routing Strategies on Urban Sustainability},
  author={Cornacchia, Giuliano and Böhm Matteo and Mauro, Giovanni and Nanni, Mirco and Pedreschi, Dino and Pappalardo, Luca},
  journal={},
  year={2022}
}
```




## How to install and configure SUMO (Simulation of Urban MObility) 🚗🚙🛻

### Install SUMO

Please always refer to the [SUMO Installation page](https://sumo.dlr.de/docs/Installing/index.html)
for the latest installation instructions.

#### > Windows

To install SUMO on Windows it is necessary to download the installer [here](https://sumo.dlr.de/docs/Downloads.php#windows) and run the executable.

#### > Linux

To install SUMO on Linux is it necessary to execute the following commands:

```
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
```

#### > macOS

SUMO can be installed on macOS via [Homebrew](https://brew.sh/).

You can install and update Homebrew as following:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
brew update
brew install --cask xquartz
```
To install SUMO:
```
brew tap dlr-ts/sumo
brew install sumo
```


### Configure SUMO

After installing SUMO you must configure your `PATH` and `SUMO_HOME` environment variables.

Suppose you installed SUMO at `/your/path/to/sumo-<version>`

#### > Windows
1. On the Windows search box search for "Edit the system environment variables" option and open it;
2. Under user variables select `PATH` and click Edit. If no such variable exists you must create it with the New-Button; 
3. Append `;/your/path/to/sumo-<version>/bin` to the end of the `PATH` value (do not delete the existing values);
4. Under user variables select `SUMO_HOME` and click Edit. If no such variable exists you must create it with the New-Button;
5. Set `/your/path/to/sumo-<version>` as the value of the `SUMO_HOME` variable.

#### > Linux

1. Open a file explorer and go to `/home/YOUR_NAME/`;
2. Open the file named `.bashrc` with a text editor;
3. Place this code export `SUMO_HOME="/your/path/to/sumo-<version>/"` somewhere in the file and save;
4. Reboot your computer.


#### > macOS

First you need to determine which shell (bash or zsh) you are currently working with. In a terminal, `type ps -p $$`.

##### ZSH

In a Terminal, execute the following steps:

1. Run the command `open ~/.zshrc`, this will open the `.zshrc` file in TextEdit;
2. Add the following line to that document: `export SUMO_HOME="/your/path/to/sumo-<version>"` and save it;
3. Apply the changes by entering: `source ~/.zshrc`.

##### bash

In a Terminal, execute the following steps:

1. Run the command `open ~/.bash_profile`, this will open the `.bash_profile` file in TextEdit;
2. Add the following line to that document: `export SUMO_HOME="/your/path/to/sumo-<version>"` and save it;
3. Apply the changes by entering: `source ~/.bash_profile`.






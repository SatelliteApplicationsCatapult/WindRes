# WindRes
A tool to create an offshore wind DB from satellite datasets, and to undertake a wind resource assessment for small areas from the created DB and/or other sources.


# The project

The research, which is contained in this thesis, was initiated with a one-year project, WindRes. This project was aimed at defining a programme of work for translating previous basic EU FP7 funded research into a commercial operational tool for satellite-enabled offshore wind resource optimization. The fundamental methodology that was to be employed had been developed and verified under the EU FP7 project NORSEWInD. The key challenges to developing commercial exploitation of this satellite-enabled technology were identified as:

- Translate NORSEWInD research into commercial, operational tools.

- Develop key applications for offshore wind and demonstrate impact.

- Demonstrate opportunities offered by satellite services in the Energy sector.

The software here available, as well as the user guide, are the results of research undertaken by author in the fulfillment of the requirements for the degree of PhD.


# Prerequisites

  - Linux/Ubuntu OS.
  - MySQL
  - Python 2.7 plus packages:
      - numpy       
      - scipy
      - pandas      
      - MySQLdb
      - netCDF4     
      - xml
      - gzip        
      - openpyxl
      - windrose    
      - matplotlib
      - basemap

      
# Installation

  ## MySQl installation
  
There are two ways of installing MySQL and MySQL Workbench. The first is the use of the Ubuntu software center. The second is the directly from the command prompt. The first option is really straightforward, thus only the second way will be explained.
Open the command prompt and type the following steps:
1.	To refresh the apt package cache to make the new software packages available.

	$	sudo apt-get update

2.	Install MySQL server.

	$	sudo apt-get mysql-server

Here it will be necessary to introduce twice the new password for the user “root”.

3.	Testing MySQL.

	$	mysqladmin –u root –p version

The password for user “root” will be asked. In the previous command, -u root refers to user, -p refers to the password. The output will be information about the MySQL version.

4.	Install MySQL Workbench.

	$	sudo apt-get mysql-workbench

5.	Run Mysql.

	$	mysql –u root –p

As step 3, the password for user “root” will be asked.
  
  ## Python 2.7 Installation
  
1.	Refresh repositories.

	$	sudo apt-get update

2.	Update all the software

	$	sudo apt-get dist-upgrade

3.	Install Python 2.7 and pip.

	$	sudo apt-get install python2.7 python-pip

  ## Python packages
  
There are two ways of installation, through pip or from the command line. It is recommended to install all packages via command line. Furthermore, some packages may need the installation of other python packages. These will be installed automatically after the user agreement. Some others may need the previous installation of Linux libraries. In these cases, instructions of installation are indicated in PiPY repository.

1.	Installation via command line (recommended).

	$	sudo apt-get install python-package_name

2.	Installation via pip.

	$	sudo pip install package_name

  ## MySQL change of directory
  
The DB size will be large, an important space is needed plus more space for the downloaded satellite datasets and csv files created prior to insertion into DB. Hence, installing an extra hard drive to the computer hosting the DB would be recommended. Thus, operating system and DB would be located in different hard drives. Once the large hard drive is installed and set to initiate when the computer turns on, the data directory can be changed. In the next steps, path2 will refer to the new directory.

1.	Stop the mysql server.

	$	sudo stop mysql

2.	Create the new directory.

	$	sudo mkdir /path2/mysql

3.	Copy over only the database folders.

	$	sudo cp –R /var/lib/mysql /path2/mysql

	$	sudo cp –R /var/lib/mysql/users /path2/mysql

4.	Copy the ibdata* and ib_logfile* files. It is necessary to copy the InnoDB tables; otherwise it will not be possible to use the tables.

	$	sudo cp –p /var/lib/mysql/ib* /path2/mysql/

5.	Backup the my.cnf file.

	$	sudo cp /etc/mysql/my.cnf /root/my.cnf.backup

6.	Edit the my.cnf file.

	$	sudo gedit /etc/mysql/my.cnf

Here, it is essential to change all mentions of the old data directory and socket to the new location. For example,
	
	datadir=/path2/mysql
	
	socket=/path2/mysql/mysql.sock

7.	Update the directory permissions.

	$	sudo chown –R mysql:mysql /path2/mysql

	$	sudo chmod 771 /path2/mysql

It may be necessary to change the permissions of each folder in the directory or path to the new containing folder.

8.	Rename the old directory.

	$	mv /var/lib/mysql /var/lib/mysql-old

9.	Let the apparmor know about the new data directory.

	$	gedit /etc/apparmor.d/usr.sbin.mysqld

As step 5, change any mention of the old directory for the new directory. This is to avoid a future issue when MySQL receives an update.

10.	Reload the apparmor profile.

	$	sudo /etc/init.d/apparmor reload

11.	Restart MySQL.

	$	sudo /etc/init.d/mysql restart

In case of the hard drive (for the new location of the DB) is not launched when the computer initiates, it will not be possible to connect with the DB. An error message will appear similar to:
	
	/var/run/mysqld/mysql.sock doesn’t exist and nor does the directory

In order to solve this issue every time the computer is initiated the steps 1, 10 and 11 must be repeated in order; i.e. stop MySQL, reload apparmor and restart MySQL. 
  
# Documentation

  Along with the scripts, there is also available a software user guide. In that manual there is further information about the software installation. The user interaction is also specified with a short example. Both blocks of the software, database creation and wins resource assessment are included with useful flowcharts for both.
  
# Author

  Alberto S. Rabaneda
  
# Acknowledgements

The project was possible due to support and advice from the University of Strathclyde, the Satellite Applications Catapult, Oldbaum Services, and the Offshore Renewable Energy Catapult.   

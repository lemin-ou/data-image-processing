import pysftp

Hostname = "test.rebex.net"
Username = "demo"
Password = "password"
port = 22
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

with pysftp.Connection(host=Hostname, username=Username, password=Password, port=port, cnopts=cnopts) as sftp:
    print("Connection successfully established ... ")
# Obtain structure of the remote directory '/opt'
    directory_structure = sftp.listdir_attr()

    # Print data
    for attr in directory_structure:
        print(attr.filename, attr)

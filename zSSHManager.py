#!/usr/bin/env python3 

from fabric import Connection, task
from invoke import Context
from paramiko import SSHException
import socket

def run_ssh_command(conn, command):
    try:
        result = conn.run(command, hide=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error executing command: {e}")
        return ""

def check_host_availability(host, user, password):
    try:
        conn = Connection(
            host=host,
            user=user,
            connect_kwargs={"password": password}
        )
        # Set the timeout value to 5 seconds
        socket.setdefaulttimeout(5)
        conn.open()
        conn.close()
        return True
    except (SSHException, socket.error):
        return False

@task
def run_command_on_servers(c):
    servers = []
    with open("servers.txt", "r") as file:
        for line in file:
            server_info = line.strip().split(",")
            server = {
                "host": server_info[0],
                "user": server_info[1],
                "password": server_info[2]
            }
            servers.append(server)

    while True:
        print(f"\nMenu:\n")
        print("1. List Hosts")
        print("2. Run Command")
        print("3. Open Shell")
        print("4. Add Server")
        print("5. Remove Server")
        print(f"6. Exit\n")
        choice = input("Enter your choice: ")

        if choice == "1":
            print(f"\nHosts:")
            available_servers = []
            for i, server in enumerate(servers):
                if check_host_availability(server["host"], server["user"], server["password"]):
                    print(f"{i}. {server['host']} (Online)")
                    available_servers.append(server)
                else:
                    print(f"{i}. {server['host']} (Offline)")
            print("-" * 30)
            servers = available_servers
        elif choice == "2":
            commands = input(f"\nEnter commands (separated by semicolon): ")
            for server in servers:
                conn = Connection(
                    host=server["host"],
                    user=server["user"],
                    connect_kwargs={"password": server["password"]}
                )
                for command in commands.split(";"):
                    try:
                        result = run_ssh_command(conn, command)
                        print(f"\nResult from {server['host']}:\n")
                        print(f"{result}\n")
                        print("-" * 30)
                    except Exception as e:
                        print(f"Error executing command on {server['host']}: {e}")
                conn.close()
        elif choice == "3":
            host_index = int(input("Enter host index: "))
            if host_index < len(servers):
                server = servers[host_index]
                conn = Connection(
                    host=server["host"],
                    user=server["user"],
                    connect_kwargs={"password": server["password"]}
                )
                try:
                    conn.run('bash', pty=True)
                except Exception as e:
                    print(f"Error opening shell on {server['host']}: {e}")
                conn.close()
            else:
                print("Invalid host index.")
        elif choice == "4":
            host = input("Enter host: ")
            user = input("Enter user: ")
            password = input("Enter password: ")
            server = {
                "host": host,
                "user": user,
                "password": password
            }
            servers.append(server)
            print("Server added successfully.")
        elif choice == "5":
            host_index = int(input("Enter host index to remove: "))
            if host_index < len(servers):
                server = servers.pop(host_index)
                print(f"Server {server['host']} removed successfully.")
            else:
                print("Invalid host index.")
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

    # Save the updated server information to the file
    with open("servers.txt", "a+") as file:
        file.seek(0)  # Move the file pointer to the beginning
        existing_servers = file.readlines()
        for server in servers:
            server_info = f"{server['host']},{server['user']},{server['password']}\n"
            if server_info not in existing_servers:
                file.write(server_info)

# Create a Context object
context = Context()

# Register the run_command_on_servers task
context.run_command_on_servers = run_command_on_servers

# Call the run_command_on_servers task
context.run_command_on_servers(context)

import socket
import cmd


class NC(cmd.Cmd):
	prompt = "> "
	
	def do_connect(self, arg):
		args = arg.split()
		match args:
			case [host, port]:
				self.s = socket.socket(socket.AF_INET, socket.SOCK_STEAM)
				self.s.connect( (host, int(port)))

	def do_print(self, arg):
		if arg:
			self.s.sendall(b"print " + arg.encode() + b'\n')
			print(self.s.recv(1024).rstrip().decode())

	def do_info(self, arg):
		match arg:
			case "host" | "port":
				self.s.sendall(b"info " + arg.encode() + b'\n')
				print(self.s.recn(1024).rstrip().decode())


if __name__ == "__main__":
	NC().cmdloop()



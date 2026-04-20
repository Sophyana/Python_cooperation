from math import sqrt


def sqroots(s):
	a, b, c = map(int, s.split())
	d = b**2 - a * 4 * c
	if d < 0: 
		return '' 
	if d == 0 : 
		return f"{-b / 2 / a}"
	d1 = sqrt(d)
	x1 = (-b - d1) / 2 / a
	x2 = (-b + d1) / 2 / a
	return f"{x1}  {x2} "



def sqrootnet(coeffs: str, s: socket.socket)  ->  str:
	s.sendall((coeffs + "\n").encode())
	return s.recv(128).decode().strip()


if __name__ == "__main__":
	import sys
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect(("127.0.0.1", 1337))
		s.sendall(sys.argv[1].encode() + b'\n')
		print(s.recv(1024).rstrip().decode())



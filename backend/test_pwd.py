import bcrypt
h = "$2b$12$s86.XXx.ZxNCq9eXwPmnkudat1YOp2VTf7u6ZBA4RQqlvFm/CPpt6".encode()
for pwd in ["test1234", "test", "password", "1234"]:
    try:
        print(f"{pwd}: {bcrypt.checkpw(pwd.encode(), h)}")
    except Exception as e:
        print(f"{pwd}: error {e}")

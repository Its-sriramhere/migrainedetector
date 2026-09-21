from app.core.security import verify_password
h = "$2b$12$s86.XXx.ZxNCq9eXwPmnkudat1YOp2VTf7u6ZBA4RQqlvFm/CPpt6"
for p in ["test1234","password","test","admin","migraine","headache","test2024"]:
    try:
        print(f"{p}: {verify_password(p, h)}")
    except Exception as e:
        print(f"{p}: error {e}")

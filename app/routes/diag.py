import socket
from fastapi import APIRouter

router = APIRouter()


@router.get("/diag/dns")
def diag_dns():
    try:
        ip = socket.gethostbyname("github.com")
        return {"host": "github.com", "ip": ip}
    except Exception as e:
        return {"error": str(e)}


@router.get("/diag/connect")
def diag_connect():
    try:
        s = socket.create_connection(("github.com", 443), timeout=5)
        s.close()
        return {"status": "connected"}
    except Exception as e:
        return {"error": str(e)}

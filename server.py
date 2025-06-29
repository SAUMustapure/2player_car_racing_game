import socket
import threading
import pickle
import time
import ssl
import random


WIDTH, HEIGHT = 800, 600
CAR_WIDTH, CAR_HEIGHT = 40, 60
BASE_VEL = 5
TRACK_WIDTH = 160
COIN_RADIUS = 10
TOTAL_COINS = 20
NITRO_DURATION_MS = 5000  
OBSTACLE_COUNT = 10


HOST = '192.168.1.3'  
PORT = 5555


players = [(100, 500), (200, 500)]
positions_lock = threading.Lock()
winner = None
game_over = False
obstacles = []
clients = [None, None]


def reliable_recv(conn):
    data = b""
    while True:
        try:
            part = conn.recv(4096)
            if not part:
                break
            data += part
            try:
                return pickle.loads(data)
            except EOFError:
                continue
        except:
            break
    return None


def generate_obstacles():
    obs = []
    for _ in range(OBSTACLE_COUNT):
        x = random.randint(WIDTH // 4, WIDTH * 3 // 4 - 40)
        y = random.randint(150, HEIGHT - 150)
        obs.append((x, y))
    return obs


def handle_client(conn, player_id, conn_info):
    global winner, game_over
    conn.settimeout(10)  # Optional timeout for inactive clients

    # Wait until both clients connect
    while None in clients:
        time.sleep(0.1)

    # Send initial game state
    try:
        conn.send(pickle.dumps((player_id, players, obstacles)))
    except:
        return

    print(f"[CONNECTED] Player {player_id} - {conn_info['version']} connection established")

    while not game_over:
        try:
            data = reliable_recv(conn)
            if data is None:
                break

            with positions_lock:
                players[player_id] = data

                # Check win condition
                if players[player_id][1] <= 50 and not winner:
                    winner = f"Player {player_id + 1}"
                    game_over = True
                    print(f"[WINNER] {winner}")

        except Exception as e:
            print(f"[ERROR] Player {player_id} recv: {e}")
            break

        try:
            conn.sendall(pickle.dumps((players, winner)))
        except Exception as e:
            print(f"[ERROR] Player {player_id} send: {e}")
            break

        time.sleep(1 / 30)  # 30 FPS tick rate

    conn.close()
    print(f"[DISCONNECTED] Player {player_id}")

# --- Main Server Function ---
def main():
    global obstacles
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # SSL setup - Modified to match the client's expectations
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    
    # The client is using CERT_REQUIRED mode, so we need to set up verification
    # even though the client doesn't actually send a certificate
    context.verify_mode = ssl.CERT_NONE  # Don't require client certificates
    
    s.bind((HOST, PORT))
    s.listen(2)

    secure = context.wrap_socket(s, server_side=True)

    print("[SERVER] Waiting for players...")

    # Generate obstacles once
    obstacles = generate_obstacles()

    # Accept two clients
    for i in range(2):
        conn, addr = secure.accept()
        
        # Get SSL connection info - client is using CERT_REQUIRED but doesn't send a certificate
        connection_info = {
            "cipher": conn.cipher(),
            "version": conn.version()
        }
        
        # Display appropriate SSL status for client which expects verification
        if conn.version() == "TLSv1.3":
            verification_status = f"SSL {connection_info['version']} Connected - Strong Encryption ({connection_info['cipher'][0]})"
        else:
            verification_status = f"SSL {connection_info['version']} Connected ({connection_info['cipher'][0]})"
        
        print(f"[ACCEPT] Player {i} from {addr} - SSL Status: {verification_status}")
        
        clients[i] = conn
        threading.Thread(target=handle_client, args=(conn, i, connection_info), daemon=True).start()

    # Wait for game to end
    while not game_over:
        time.sleep(0.1)

    # Final broadcast
    for c in clients:
        try:
            c.sendall(pickle.dumps((players, winner)))
        except:
            pass

    # Cleanup
    for c in clients:
        try:
            c.close()
        except:
            pass

    print("[SERVER] Game ended.")

if __name__ == "__main__":
    main()
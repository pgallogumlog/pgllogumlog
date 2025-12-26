"""Kill all old server processes."""
import subprocess
import time

print("Killing all Python server processes...")

# Method 1: Kill by PID
old_pids = [154880, 185308, 183600, 180776, 193384]
for pid in old_pids:
    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid), '/T'],
                      capture_output=True, shell=True)
        print(f"  Killed PID {pid}")
    except Exception as e:
        print(f"  Could not kill {pid}: {e}")

time.sleep(3)

# Verify
result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
listening = [line for line in result.stdout.split('\n') if ':8000' in line and 'LISTENING' in line]

print(f"\nVerification - Processes on port 8000: {len(listening)}")
for line in listening:
    print(f"  {line.strip()}")

if len(listening) == 0:
    print("\n✓ All servers killed successfully!")
else:
    print(f"\n✗ Warning: {len(listening)} processes still listening on port 8000")

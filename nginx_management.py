import os
import sys

# 配置文件目录路径
conf_dir = "./conf"
# NGINX 可执行文件路径
nginx_path = "./sbin/nginx"


def start_nginx():
    print("Starting NGINX...")
    conf_files = [os.path.join(conf_dir, f) for f in os.listdir(conf_dir) if f.startswith("nginx_") and f.endswith(".conf")]
    conf_files = sorted(conf_files, key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
    for conf_file in conf_files:
        print(f"Starting NGINX with config file: {conf_file}")
        os.system(f"{nginx_path} -c {conf_file}")


def stop_nginx():
    print("Stopping NGINX...")
    conf_files = [os.path.join(conf_dir, f) for f in os.listdir(conf_dir) if f.startswith("nginx_") and f.endswith(".conf")]
    conf_files = sorted(conf_files, key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
    for conf_file in conf_files:
        print(f"Stopping NGINX with config file: {conf_file}")
        os.system(f"{nginx_path} -c {conf_file} -s stop")


def check_nginx_status():
    print("Checking NGINX status...")
    conf_files = [os.path.join(conf_dir, f) for f in os.listdir(conf_dir) if f.startswith("nginx_") and f.endswith(".conf")]
    conf_files = sorted(conf_files, key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
    for conf_file in conf_files:
        # 提取配置文件中的 pid 文件名
        with open(conf_file, 'r') as f:
            content = f.read()
            for line in content.splitlines():
                if line.strip().startswith('pid'):
                    pid_file = line.split(' ')[-1].rstrip(';')
                    pid_file = os.path.join(os.getcwd(), 'logs', os.path.basename(pid_file))
                    break

        try:
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            # 检查该 pid 是否存在
            ps_output = os.popen(f"ps -p {pid} -o comm=").read().strip()
            if ps_output:
                print(f"NGINX instance with config {conf_file} is running (PID: {pid}).")
            else:
                print(f"NGINX instance with config {conf_file} is not running.")
        except FileNotFoundError:
            print(f"PID file {pid_file} not found for config {conf_file}.")


def generate_config_files(start_port, port_count, ipv4=True, ipv6=True):
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)

    num_files = (port_count + 499) // 500
    # 计算数字的最大位数
    max_digits = len(str(num_files - 1))
    for i in range(num_files):
        start = start_port + i * 500
        end = min(start + 499, start_port + port_count - 1)
        # 补零处理
        padded_index = str(i).zfill(max_digits)
        conf_content = f"""
#user  nobody;
worker_processes  1;
pid        logs/nginx_{padded_index}.pid;
events {{
    worker_connections  10240;
}}
http {{
    include       mime.types;
    default_type  application/octet-stream;
    sendfile        on;
    keepalive_timeout  65;
    server {{
"""
        listen_lines = []
        if ipv4:
            listen_lines.append(f"        listen       {start}-{end};")
        if ipv6:
            listen_lines.append(f"        listen       [::]:{start}-{end};")
        conf_content += "\n".join(listen_lines)
        conf_content += f"""
        server_name  _;
        location / {{
            root   html;
            index  index.html index.htm;
        }}
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {{
            root   html;
        }}
    }}
}}
"""
        conf_file = os.path.join(conf_dir, f"nginx_{padded_index}.conf")
        with open(conf_file, "w") as f:
            f.write(conf_content)
        print(f"Generated config file: {conf_file}")

def delete_config_files():
    print("Deleting configuration files...")
    if os.path.exists(conf_dir):
        conf_files = [os.path.join(conf_dir, f) for f in os.listdir(conf_dir) if f.startswith("nginx_") and f.endswith(".conf")]
        conf_files = sorted(conf_files, key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
        for conf_file in conf_files:
            try:
                os.remove(conf_file)
                print(f"Deleted configuration file: {conf_file}")
            except OSError as e:
                print(f"Error deleting {conf_file}: {e}")
    else:
        print("Configuration directory does not exist.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nginx_management.py [start [N]|stop|status|generate <start_port> <port_count> [--ipv4] [--ipv6]|delete]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "start":
        if len(sys.argv) > 2:
            try:
                num_instances = int(sys.argv[2])
                start_nginx(num_instances)
            except ValueError:
                print("Invalid number of instances. Please provide a valid integer.")
                sys.exit(1)
        else:
            start_nginx()
    elif command == "stop":
        stop_nginx()
    elif command == "status":
        check_nginx_status()
    elif command == "generate":
        if len(sys.argv) < 4:
            print("Usage: python nginx_management.py generate <start_port> <port_count> [--ipv4] [--ipv6]")
            sys.exit(1)
        start_port = int(sys.argv[2])
        port_count = int(sys.argv[3])
        ipv4 = "--ipv4" in sys.argv
        ipv6 = "--ipv6" in sys.argv
        if not ipv4 and not ipv6:
            ipv4 = ipv6 = True
        generate_config_files(start_port, port_count, ipv4, ipv6)
    elif command == "delete":
        delete_config_files()
    else:
        print("Usage: python nginx_management.py [start [N]|stop|status|generate <start_port> <port_count> [--ipv4] [--ipv6]|delete]")
    
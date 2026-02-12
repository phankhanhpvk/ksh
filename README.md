# ksh - Plugin Zsh hỗ trợ SSH nhanh 

**ksh** là một plugin Oh My Zsh giúp quản lý và kết nối SSH nhanh chóng đến các server. Sử dụng Python để đồng bộ instance từ AWS.

## Tính năng

### 🚀 Kết nối thông minh
- **Tìm kiếm mờ (Fuzzy Search):** Sử dụng `fzf` để tìm kiếm server theo Alias hoặc IP cực nhanh.
- **Hỗ trợ Jump Host:** Dễ dàng kết nối qua jump host chỉ với một lệnh.
- **Tương thích:** Tự động đọc và parse `~/.ssh/config` hiện có.

### ☁️ Đồng bộ AWS EC2 (Siêu tốc)
- **Parallel Sync:** Quét tất cả AWS Regions song song, giảm thời gian đồng bộ từ phút xuống giây.
- **Tự động hóa:** Tự động tạo file config (`~/.ssh/ksh_ec2_config`) và include vào file chính.
- **Linh hoạt:** Cấu hình lọc server theo tên (Regex), loại trừ Spot instance, ưu tiên Private IP, v.v.

---

## Cài đặt

### Yêu cầu
- **Zsh** & **Oh My Zsh**
- **AWS CLI** (đã cấu hình `aws configure`)
- **Python 3**
- **fzf** (khuyên dùng để có trải nghiệm tốt nhất)

### Cài đặt Plugin
1. Clone repository vào thư mục plugin của Oh My Zsh:
   ```bash
   git clone https://github.com/phankhanhpvk/ksh.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/ksh
   ```

2. Thêm `ksh` vào danh sách plugins trong `~/.zshrc`:
   ```zsh
   plugins=(... ksh)
   ```

3. Reload lại shell:
   ```bash
   source ~/.zshrc
   ```

---

## Sử dụng

### 1. Kết nối SSH
Sử dụng lệnh `ksh` để tìm kiếm và kết nối:

```bash
ksh [tên-server-hoặc-ip]
```

- Nếu không nhập tham số: Mở giao diện tìm kiếm `fzf`.
- Nếu nhập tham số: Tìm chính xác hoặc gần đúng server đầu tiên.

### 2. Kết nối qua Jump Host
Sử dụng `kshj` hoặc `ksh --jump` để kết nối thông qua Jump Host (mặc định là `sb-monitor`):

```bash
kshj my-private-server
```

*(Lưu ý: Cần đảm bảo host `sb-monitor` đã được định nghĩa trong ssh config của bạn)*

### 3. (Optional) fzf
Để có trải nghiệm tìm kiếm tốt nhất, hãy cài đặt `fzf`. Plugin sẽ tự động sử dụng `fzf` nếu có.

```bash
# MacOS
brew install fzf

# Ubuntu/Debian
sudo apt-get install fzf
```



### 4. Đồng bộ EC2 (Sync)
Lệnh đồng bộ danh sách server từ AWS:

```bash
ksh --sync
```

### Cấu hình Sync (trong `~/.zshrc`)

Bạn có thể tùy chỉnh hành vi sync bằng các biến môi trường sau:

| Biến Môi Trường | Mô tả | Ví dụ |
| :--- | :--- | :--- |
| `KSH_JUMP_HOST` | Jump Host mặc định (khi dùng `--jump` hoặc `kshj`) | `sb-monitor` |
| `KSH_JUMP_HOST_<REGION>` | Jump Host cho region cụ thể (dùng khi jump được bật) | `jump-host-use1` |
| `KSH_SYNC_NO_SPOT` | Bỏ qua các Spot Instances (True/False) | `true` |
| `KSH_SYNC_PRIVATE_IP` | Luôn sử dụng Private IP thay vì Public IP | `true` |
| `KSH_SYNC_EXCLUDE_REGEX` | Regex để loại trừ các server theo tên | `.*(test|dev).*` |
| `KSH_SYNC_USER` | SSH User mặc định cho các server được sync | `ubuntu` |
| `KSH_SYNC_PORT` | SSH Port mặc định | `22` |

**Ví dụ cấu hình:**
```zsh
export KSH_SYNC_NO_SPOT=true
export KSH_SYNC_USER=ec2-user
export KSH_SYNC_EXCLUDE_REGEX="^eks-.*"
```

---

## Cấu trúc Project
Plugin được tổ chức theo mô hình module Python hiện đại:

```
ksh/
├── ksh.plugin.zsh          # Entry point cho Zsh
└── src/
    ├── main.py             # Script chính
    ├── core/               # Config & Logging
    ├── providers/          # Các module cloud (AWS)
    └── utils/              # Tiện ích bổ trợ (SSH Config)
```

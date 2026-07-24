# SoilGrids Data Download

## English

Query and download ISRIC SoilGrids soil property data — free, no API key required.

### Installation

**ClawHub:**
```bash
clawhub install soilgrids-download
```

**Claude Code / skills.sh:**
```bash
claude skills install soilgrids-download
```

**Manual:**
```bash
git clone <repo-url> soilgrids-download
cd soilgrids-download
pip install requests tqdm
```

### Quick Start

```bash
# Query soil pH at a point
python scripts/soilgrids_download.py query \
  --property phh2o \
  --lat 39.9042 --lon 116.4074 \
  --output beijing_ph.csv

# List all available properties
python scripts/soilgrids_download.py list-properties
```

### Data Source

- **API**: https://rest.isric.org/soilgrids/v2.0/
- **License**: CC-BY 4.0 (ISRIC)
- **Citation**: Poggio, L., et al., 2021. SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL, 7, 217-240.

---

## 中文

查询和下载 ISRIC SoilGrids 土壤属性数据 —— 完全免费，无需 API 密钥。

### 安装

**ClawHub:**
```bash
clawhub install soilgrids-download
```

**Claude Code / skills.sh:**
```bash
claude skills install soilgrids-download
```

**手动安装:**
```bash
git clone <repo-url> soilgrids-download
cd soilgrids-download
pip install requests tqdm
```

### 快速开始

```bash
# 查询北京某点土壤 pH
python scripts/soilgrids_download.py query \
  --property phh2o \
  --lat 39.9042 --lon 116.4074 \
  --output beijing_ph.csv

# 列出所有可用属性
python scripts/soilgrids_download.py list-properties
```

### 数据来源

- **API**: https://rest.isric.org/soilgrids/v2.0/
- **许可证**: CC-BY 4.0 (ISRIC)
- **引用**: Poggio, L., et al., 2021. SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL, 7, 217-240.

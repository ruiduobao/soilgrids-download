---
description: 'Download ISRIC SoilGrids soil property data including pH, organic carbon,
  sand/silt/clay

  fractions, bulk density, and cation exchange capacity. Supports point queries

  (and bbox center-point queries) across 6 standard depth layers at 250m resolution.

  '
name: soilgrids-download
---

# SoilGrids Data Download

Query and download global soil property data from ISRIC SoilGrids — free, no API key required.

## Overview

SoilGrids is a system for global digital soil mapping produced by ISRIC — World Soil Information.
It provides predictions for standard soil properties at 6 standard depth intervals at 250m resolution,
using machine learning models trained on global soil profile databases and environmental covariates.

## Features

- **Soil properties**: pH(H₂O), organic carbon, sand/silt/clay fractions, bulk density, CEC, etc.
- **6 depth layers**: 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm
- **Point and bbox center-point queries**: single location or bbox center
- **Output formats**: CSV, JSON
- **No API key required**: completely free and open
- **Property coverage info**: shows which depths are available for each property

## Key Properties

| Property | Description | Unit |
|----------|-------------|------|
| phh2o | Soil pH in H₂O | pH×10 |
| soc | Soil Organic Carbon | g/kg |
| sand | Sand fraction | g/kg |
| silt | Silt fraction | g/kg |
| clay | Clay fraction | g/kg |
| bdv | Bulk Density (fine earth) | cg/cm³ |
| cec | Cation Exchange Capacity | mmol(c)/kg |
| nitrogen | Total Nitrogen | g/kg |
| ocs | Organic Carbon Stock | t/ha |

## Usage

```bash
# Query soil pH at a point
python scripts\soilgrids_download.py query \
  --property phh2o \
  --lat 39.9042 --lon 116.4074 \
  --output beijing_ph.csv

# Query multiple properties for a region (uses bbox center point)
python scripts\soilgrids_download.py query \
  --property phh2o,soc,sand,silt,clay \
  --bbox 73 18 135 54 \
  --depth 0-5,5-15 \
  --output china_soil.json --format json

# List all available properties
python scripts\soilgrids_download.py list-properties

# List available depth layers
python scripts\soilgrids_download.py list-depths

# Query organic carbon stock
python scripts\soilgrids_download.py query \
  --property ocs \
  --lat 31.2304 --lon 121.4737 \
  --output shanghai_carbon.csv
```

## Parameters

- `--property`: Comma-separated property names (default: phh2o)
- `--lat/--lon`: Point coordinates (WGS84)
- `--bbox`: Bounding box as `west south east north`
- `--depth`: Comma-separated depth intervals (default: 0-5,5-15,15-30,30-60,60-100,100-200)
- `--output`: Output file path
- `--format`: `csv` or `json`

## Installation

```bash
# Install dependencies
pip install requests>=2.28.0 tqdm

# Or install from requirements.txt
pip install -r scripts/requirements.txt
```

## Data Source

- **API**: https://rest.isric.org/soilgrids/v2.0/
- **Documentation**: https://www.isric.org/explore/soilgrids/faq-soilgrids
- **License**: CC-BY 4.0 (ISRIC)
- **Rate Limit**: No strict limit; recommended max 5 requests/minute for stable access
- **Citation**: Poggio, L., et al., 2021. SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL, 7, 217-240.

### Citation Format

```bibtex
@article{poggio2021soilgrids,
  title={SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty},
  author={Poggio, L. and others},
  journal={SOIL},
  volume={7},
  pages={217--240},
  year={2021},
  doi={10.5194/soil-7-217-2021}
}
```

### Units Conversion

Raw values require conversion for standard units:

| Property | Raw Unit | Standard Unit | Conversion |
|----------|----------|---------------|------------|
| phh2o | pH×10 | pH | Divide by 10 |
| soc | g/kg | g/kg | No conversion |
| sand | g/kg | g/kg | No conversion |
| silt | g/kg | g/kg | No conversion |
| clay | g/kg | g/kg | No conversion |
| bdv | cg/cm³ | g/cm³ | Divide by 100 |
| cec | mmol(c)/kg | mmol(c)/kg | No conversion |
| nitrogen | g/kg | g/kg | No conversion |
| ocs | t/ha | t/ha | No conversion |

### Missing Data Handling

- Unavailable layers are represented as `NaN` in output.
- Some properties are not available at all depth layers — check `list-properties` for coverage.

### Command Examples

**list-properties** output:
```
Property: phh2o
  Available depths: 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm
  Unit: pH×10
  Description: Soil pH in H2O
```

**list-depths** output:
```
Depth intervals (cm):
  0-5    (sl1)
  5-15   (sl2)
  15-30  (sl3)
  30-60  (sl4)
  60-100 (sl5)
  100-200(sl6)
```

### Data Uncertainty

SoilGrids provides quantile predictions:
- **P5**: 5th percentile (lower bound)
- **P50**: 50th percentile (median prediction)
- **P95**: 95th percentile (upper bound)

Use P50 as the best estimate; P5–P95 range indicates prediction uncertainty.

### GIS Integration

- **QGIS**: Load CSV via `Layer → Add Layer → Add Delimited Text Layer`, set X=longitude, Y=latitude.
- **Python/GDAL**: Convert to raster with `gdal_rasterize` or `rasterio`:
  ```python
  import geopandas as gpd
  gdf = gpd.read_file('output.csv')  # or convert from CSV with geometry
  gdf.to_file('output.shp')
  ```

### Visualization

- **Depth profiles**: Plot property values across depth layers (0–200cm) as bar/line charts.
- **Spatial distribution**: Load in QGIS and apply classified color ramps.
- **Uncertainty maps**: Map P50 and (P95 - P5) side by side.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issue or API down | Check internet connection, retry in 1 minute |
| `HTTP 429` | Rate limit exceeded | Wait 60 seconds before retrying |
| `HTTP 404` | Invalid parameters or date range | Check parameter names and date format |
| `ValueError: bbox` | Invalid bounding box | Ensure format is `west,south,east,north` |
| Empty output | No data for query region/time | Try different date range or check coordinates |
| `ModuleNotFoundError` | Missing dependency | Run `pip install requests tqdm` |

---

## Advanced Usage

### Batch Point Query
```bash
# Query multiple points from a CSV
while IFS=',' read -r id lat lon; do
  python scripts\soilgrids_download.py query --lat $lat --lon $lon --property clay --depth 0-5cm --output clay_${id}.csv
  sleep 0.5
done < points.csv
```

### CI/CD Integration (GitHub Actions)
```yaml
# .github/workflows/update-soilgrids.yml
name: Update Soil Data
on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly
jobs:
  download:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: |
          python scripts\soilgrids_download.py query \
            --lat 39.9 --lon 116.4 --property phh2o \
            --depth 0-5cm --output china_ph.csv
```

### PostgreSQL/PostGIS Import
```bash
python scripts\soilgrids_download.py query --lat 39.9 --lon 116.4 --property clay --depth 0-5cm --output soil.csv

psql -d gis_db -c "\COPY soil_samples(id, lat, lon, clay_pct) FROM 'soil.csv' CSV HEADER"
```

### Performance Tips
- Add `sleep 0.5` between point queries to respect rate limits
- Use `--format csv` for tabular analysis, `--format json` for web apps
- Unit conversion: phh2o × 0.1 = pH in standard units; bdv (bulk density) in g/cm³
- For bbox queries, the tool calculates the center point and queries that location

---

## 中文说明

从 ISRIC SoilGrids 查询和下载全球土壤属性数据 —— 包括 pH、有机碳、砂粒/粉粒/粘粒含量、容重、阳离子交换量等。完全免费，无需 API 密钥。

### 核心功能

- **土壤属性**：pH(H₂O)、有机碳、砂粒/粉粒/粘粒含量、容重、CEC 等
- **6 个标准深度层**：0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm
- **点查询和区域中心点查询**：单点经纬度或边界框中心点
- **输出格式**：CSV、JSON
- **无需 API 密钥**：完全免费开放
- **属性覆盖信息**：显示每个属性在哪些深度可用

### 主要属性

| 属性名 | 描述 | 单位 |
|--------|------|------|
| phh2o | 土壤 pH（水浸提） | pH×10 |
| soc | 土壤有机碳 | g/kg |
| sand | 砂粒含量 | g/kg |
| silt | 粉粒含量 | g/kg |
| clay | 粘粒含量 | g/kg |
| bdv | 容重（细粒土） | cg/cm³ |
| cec | 阳离子交换量 | mmol(c)/kg |
| nitrogen | 全氮 | g/kg |
| ocs | 有机碳储量 | t/ha |

### 使用示例

```bash
# 查询北京某点土壤 pH
python scripts\soilgrids_download.py query \
  --property phh2o \
  --lat 39.9042 --lon 116.4074 \
  --output beijing_ph.csv

# 查询中国区域多种土壤属性（使用边界框中心点）
python scripts\soilgrids_download.py query \
  --property phh2o,soc,sand,silt,clay \
  --bbox 73 18 135 54 \
  --depth 0-5,5-15 \
  --output china_soil.json --format json

# 列出所有可用属性
python scripts\soilgrids_download.py list-properties

# 列出可用深度层
python scripts\soilgrids_download.py list-depths

# 查询上海有机碳储量
python scripts\soilgrids_download.py query \
  --property ocs \
  --lat 31.2304 --lon 121.4737 \
  --output shanghai_carbon.csv
```

### 数据来源

- **API**: https://rest.isric.org/soilgrids/v2.0/
- **文档**: https://www.isric.org/explore/soilgrids/faq-soilgrids
- **许可证**: CC-BY 4.0 (ISRIC)
- **引用**: Poggio, L., et al., 2021. SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. SOIL, 7, 217-240.

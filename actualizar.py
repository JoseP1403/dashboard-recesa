import pandas as pd
import numpy as np
import json
import re
import calendar
from pathlib import Path

EXCEL_FILE = "Base_Maestra_Vendedores_RECESA.xlsx"
OUTPUT_FILE = "datos.json"

month_order = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4,
    "may": 5, "jun": 6, "jul": 7, "ago": 8,
    "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

month_labels_short = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}

month_labels_full = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def mes_num(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().lower()
    parts = re.split(r"\s+|-|/", text)
    for part in parts:
        if part in month_order:
            return month_order[part]
    return month_order.get(text)


def validate_columns(df):
    required_columns = [
        "Vendedor", "Codigo", "Descripcion", "Categoria",
        "Mes", "Total", "Cantidad", "Precio_Promedio", "Año",
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(
            "Faltan estas columnas en el Excel: " + ", ".join(missing)
        )


def main():
    excel_path = Path(EXCEL_FILE)

    if not excel_path.exists():
        raise FileNotFoundError(
            f"No encontré el archivo {EXCEL_FILE}. "
            "Asegúrate de que esté en la misma carpeta que actualizar.py"
        )

    df = pd.read_excel(excel_path)

    validate_columns(df)

    df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
    df["Cantidad"] = pd.to_numeric(df["Cantidad"], errors="coerce").fillna(0)
    df["Año"] = pd.to_numeric(df["Año"], errors="coerce").fillna(0).astype(int)

    df["Mes_Num"] = df["Mes"].apply(mes_num)

    if df["Mes_Num"].isna().any():
        meses_no_reconocidos = df.loc[df["Mes_Num"].isna(), "Mes"].unique()
        raise ValueError(
            "Hay meses que no pude reconocer: "
            + ", ".join(map(str, meses_no_reconocidos))
        )

    df = df.sort_values(["Año", "Mes_Num"])

    # ── Resumen mensual total ─────────────────────────────
    monthly = (
        df.groupby(["Año", "Mes_Num"], as_index=False)
        .agg(total=("Total", "sum"), units=("Cantidad", "sum"))
        .sort_values(["Año", "Mes_Num"])
    )

    labels = [
        month_labels_short[int(row.Mes_Num)] + str(int(row.Año))[2:]
        for row in monthly.itertuples()
    ]

    full_labels = [
        f"{month_labels_full[int(row.Mes_Num)]} {int(row.Año)}"
        for row in monthly.itertuples()
    ]

    totals = [round(float(v), 2) for v in monthly["total"]]
    units  = [int(round(float(v))) for v in monthly["units"]]

    # ── Por vendedor mensual ──────────────────────────────
    vendedores = sorted(df["Vendedor"].dropna().unique().tolist())

    pivot = (
        df.pivot_table(
            index=["Año", "Mes_Num"],
            columns="Vendedor",
            values="Total",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    pivot = (
        monthly[["Año", "Mes_Num"]]
        .merge(pivot, on=["Año", "Mes_Num"], how="left")
        .fillna(0)
    )

    vendedor_series = {}
    for v in vendedores:
        if v in pivot.columns:
            vendedor_series[v] = [round(float(x), 2) for x in pivot[v]]
        else:
            vendedor_series[v] = [0] * len(pivot)

    # ── Totales por vendedor ──────────────────────────────
    vendor_totals = (
        df.groupby("Vendedor")
        .agg(total=("Total", "sum"), units=("Cantidad", "sum"))
    )

    vendor_summary = {}
    for v in vendedores:
        if v in vendor_totals.index:
            vt = round(float(vendor_totals.loc[v, "total"]), 2)
            vu = int(round(float(vendor_totals.loc[v, "units"])))
            grand = round(float(vendor_totals["total"].sum()), 2)
            pct = round((vt / grand * 100), 1) if grand > 0 else 0

            # Categoría top
            cat_top = (
                df[df["Vendedor"] == v]
                .groupby("Categoria")["Total"].sum()
                .idxmax()
            )

            # Precio promedio
            precio_prom = round(float(
                df[df["Vendedor"] == v]["Precio_Promedio"].mean()
            ), 2)

            vendor_summary[v] = {
                "total":       vt,
                "units":       vu,
                "pct":         pct,
                "topCategory": cat_top,
                "avgPrice":    precio_prom,
            }
        else:
            vendor_summary[v] = {
                "total": 0, "units": 0, "pct": 0,
                "topCategory": "", "avgPrice": 0,
            }

    # ── Categorías por vendedor ───────────────────────────
    vendor_categories = {}
    for v in vendedores:
        cat_df = (
            df[df["Vendedor"] == v]
            .groupby("Categoria", as_index=False)
            .agg(total=("Total", "sum"), units=("Cantidad", "sum"))
            .sort_values("total", ascending=False)
        )
        vendor_categories[v] = [
            {
                "name":  str(row.Categoria),
                "total": round(float(row.total), 2),
                "units": int(round(float(row.units))),
            }
            for row in cat_df.itertuples()
        ]

    # ── Top productos global ──────────────────────────────
    products_df = (
        df.groupby("Descripcion", as_index=False)
        .agg(total=("Total", "sum"), units=("Cantidad", "sum"))
        .sort_values("total", ascending=False)
        .head(8)
    )

    products = [
        {
            "name": str(row.Descripcion),
            "val":  round(float(row.total), 2),
        }
        for row in products_df.itertuples()
    ]

    # ── Top categoría global ──────────────────────────────
    top_category_df = (
        df.groupby("Categoria", as_index=False)
        .agg(units=("Cantidad", "sum"))
        .sort_values("units", ascending=False)
    )
    top_category       = str(top_category_df.iloc[0]["Categoria"])
    top_category_units = int(round(float(top_category_df.iloc[0]["units"])))

    # ── Detalle mensual ───────────────────────────────────
    details = []
    for (year, month), group in df.groupby(["Año", "Mes_Num"], sort=True):
        total = float(group["Total"].sum())
        qty   = float(group["Cantidad"].sum())

        days_in_month = calendar.monthrange(int(year), int(month))[1]

        product_summary = (
            group.groupby("Descripcion", as_index=False)
            .agg(total=("Total", "sum"), units=("Cantidad", "sum"))
        )

        top_value = product_summary.sort_values("total", ascending=False).iloc[0]
        top_u     = product_summary.sort_values("units", ascending=False).iloc[0]

        vendor_month = {}
        for v in vendedores:
            vendor_month[v] = round(
                float(group.loc[group["Vendedor"] == v, "Total"].sum()), 2
            )

        details.append({
            "month":           f"{month_labels_full[int(month)]} {int(year)}",
            "total":           round(total, 2),
            "units":           int(round(qty)),
            "daily":           round(total / days_in_month, 2),
            "byVendor":        vendor_month,
            "topValueProduct": str(top_value["Descripcion"]),
            "topValueTotal":   round(float(top_value["total"]), 2),
            "topUnitsProduct": str(top_u["Descripcion"]),
            "topUnitsQty":     int(round(float(top_u["units"]))),
        })

    # ── Mejor mes ─────────────────────────────────────────
    best_index = int(np.argmax(totals))

    grand_total = round(sum(totals), 2)
    grand_units = int(sum(units))

    # ── Precio promedio global ────────────────────────────
    avg_price = round(grand_total / grand_units, 2) if grand_units > 0 else 0

    # ── Output JSON ───────────────────────────────────────
    datos = {
        "labels":          labels,
        "fullLabels":      full_labels,
        "totals":          totals,
        "units":           units,
        "vendedores":      vendedores,
        "vendedorSeries":  vendedor_series,
        "vendedorSummary": vendor_summary,
        "vendedorCategories": vendor_categories,
        "grandTotal":      grand_total,
        "grandUnits":      grand_units,
        "avgPrice":        avg_price,
        "topCategory":     top_category,
        "topCategoryUnits": top_category_units,
        "products":        products,
        "details":         details,
        "bestMonth":       full_labels[best_index],
        "bestTotal":       totals[best_index],
        "periodLabel":     f"{full_labels[0]} – {full_labels[-1]}",
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print("✓ datos.json generado correctamente")
    print(f"  Ventas totales : Q{grand_total:,.2f}")
    print(f"  Unidades       : {grand_units:,}")
    print(f"  Precio promedio: Q{avg_price:,.2f}")
    print(f"  Top categoría  : {top_category} ({top_category_units:,} uds.)")
    print(f"  Mejor mes      : {full_labels[best_index]} (Q{totals[best_index]:,.2f})")
    print(f"  Período        : {full_labels[0]} – {full_labels[-1]}")
    for v in vendedores:
        s = vendor_summary[v]
        print(f"  {v:10s}: Q{s['total']:>12,.2f}  ({s['pct']}%)")


if __name__ == "__main__":
    main()

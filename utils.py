import pandas as pd
import google.generativeai as genai

genai.configure(api_key='AIzaSyBwIszYIXYkhpNO2cRqQ_LNtQjU9MW3V7c')
def load_data(file_path):
    data = pd.read_excel(file_path)
    return data

def process_service_data(df, year, month):
    # Initialize the final DataFrame
    final_df = pd.DataFrame(columns=df.columns[1:])

    # Select data for the specified year and month
    df1 = df.loc[(year, month)]

    for k in df1.index.unique():
        df2 = df1.loc[k]
        columns_to_check = ['Service Hours Billed', 'Cost of Service Rate Billed',
                            'Cost of Service Delivery Hour']

        df_sku = pd.DataFrame(columns=df.columns[1:])
        df_wo = pd.DataFrame(columns=df.columns[1:])

        for i in range(len(df2)):
            if df2.iloc[i][columns_to_check].isna().all():
                df_row_sku = pd.DataFrame([df2.iloc[i, 1:]])
                df_row_sku['Product'] = k  # Adding product information in a separate column
                df_row_sku['Type'] = 'SKU'  # Set Type to 'SKU'
                df_sku = pd.concat([df_sku, df_row_sku], ignore_index=True)
            else:
                df_row_wo = pd.DataFrame([df2.iloc[i, 1:]])
                df_row_wo['Product'] = k  # Adding product information in a separate column
                df_row_wo['Type'] = 'WO'  # Set Type to 'WO'
                df_wo = pd.concat([df_wo, df_row_wo], ignore_index=True)

        # Concatenate the data for this iteration and add to the final DataFrame
        final_df = pd.concat([final_df, df_sku, df_wo], ignore_index=True)

    # Reorder the columns for readability
    cols_order = ['Product', 'Type'] + list(final_df.columns[0:-2])  # Adjust as necessary
    final_df1 = final_df[cols_order]

    return final_df1

def calculate_totals(final_df, year, month, product):
    sku_df = final_df[
        (final_df['Product'] == product) & (final_df['Type'] == 'SKU')
    ]
    # Calculate values for product with type SKU
    sku_units_sold = (sku_df['Units Sold'].sum())
    sku_sale_price = (sku_df['Sale Price'].mean())
    sku_cost_of_production = sku_df['Cost of Production per Unit'].mean()
    sku_total_sale = sku_units_sold * sku_sale_price

    # Filter DataFrame for product with type WO
    wo_df = final_df[
        (final_df['Product'] == product) & (final_df['Type'] == 'WO')
    ]
    # Calculate values for product with type WO
    wo_units_sold = (wo_df['Units Sold'].sum())
    wo_sale_price = (wo_df['Sale Price'].mean() if wo_df['Sale Price'].notna().any() else 0)
    wo_cost_of_production = wo_df['Cost of Production per Unit'].mean()
    wo_service_hours_billed = wo_df['Service Hours Billed'].sum()
    wo_cost_of_service_rate_billed = wo_df['Cost of Service Rate Billed'].mean()
    wo_cost_of_service_delivery_hour = wo_df['Cost of Service Delivery Hour'].mean()
    wo_total_sale= wo_service_hours_billed * wo_cost_of_service_rate_billed

    return {
        'Product': product,
        'SKU': {
            'Units Sold': sku_units_sold,
            'Sale Price': sku_sale_price,
            'Cost of Production per Unit': sku_cost_of_production,
            'Total Sale': sku_total_sale,
        },
        'WO': {
            'Units Sold': wo_units_sold,
            'Sale Price': wo_sale_price,
            'Cost of Production per Unit': wo_cost_of_production,
            'Service Hours Billed': wo_service_hours_billed,
            'Cost of Service Rate Billed': wo_cost_of_service_rate_billed,
            'Cost of Service Delivery Hour': wo_cost_of_service_delivery_hour,
            'Total Sale': wo_total_sale
        }
    }


def generate_report(year, month, year1, month1, product_lines,final_dataframe1, final_dataframe2):
    header = [
        "Product Line", "Type",
        "Units Sold", "Sale Price", "Cost Of Production per Unit",
        "Service Hours Billed", "Cost of Service Rate Billed",
        "Cost of Service Delivery Hour",
        "Units Sold1", "Sale Price1", "Cost Of Production per Unit1",
        "Service Hours Billed1", "Cost of Service Rate Billed1",
        "Cost of Service Delivery Hour1",
        "Prior Total Sales", "Current Total Sales","Price Variation", "Price Effect",
        "Volume Variation","Volume Effect","Mix Effect", "Total Revenue Change",
        "Prior Total Cost" ,"Current  Total Cost", "Q1 GP Margin", "Q2 GP Margin",
        "GP Margin Change", "Margin Variation", "Margin Price Effect","Volume Variation.1",
        "Margin Volume Effect", "Margin Mix Effect", "Total Margin Change",
        "Revenue Growth Rate ", "Revenue Price Effect (%)", "Revenue Volume Effect (%)",
        "Revenue Mix Effect (%)", "KPI total ","Margin Growth Rate","Margin Price Effect (%)",
        "Margin Volume Effect (%)","Margin Mix Effect (%)","KPI total"





    ]

    report_data = []

    for product in product_lines:
        totals_current = calculate_totals(final_dataframe1, year, month, product)
        totals_next = calculate_totals(final_dataframe2, year1, month1, product)

        # SKU data
        prior_total_sales = totals_current['SKU']['Total Sale']
        current_total_sales = totals_next['SKU']['Units Sold'] * totals_next['SKU']['Sale Price']
        price_variation = totals_next['SKU']['Sale Price'] - totals_current['SKU']['Sale Price']
        price_effect = price_variation * totals_current['SKU']['Units Sold']
        volume_variation = totals_next['SKU']['Units Sold'] - totals_current['SKU']['Units Sold']
        volume_effect = volume_variation * totals_current['SKU']['Sale Price']
        mix_effect = (current_total_sales - prior_total_sales) - price_effect - volume_effect
        total_revenue_change = price_effect + volume_effect + mix_effect
        try:
            revenue_price_effect = price_effect / total_revenue_change
            revenue_volume_effect = volume_effect / total_revenue_change
            revenue_mix_effect =( mix_effect / total_revenue_change)
            revenue_growth_rate = ((current_total_sales - prior_total_sales) / prior_total_sales) * 100
        except ZeroDivisionError:
            revenue_price_effect = 0
            revenue_volume_effect = 0
            revenue_mix_effect = 0
            revenue_growth_rate = 0
        effect=revenue_mix_effect*100
        prior_total_cost = totals_current['SKU']['Units Sold'] * totals_current['SKU']['Cost of Production per Unit']
        current_total_cost = totals_next['SKU']['Units Sold'] * totals_next['SKU']['Cost of Production per Unit']
        q1_gp_margin = prior_total_sales - prior_total_cost
        q2_gp_margin = current_total_sales - current_total_cost
        gp_margin_change = q2_gp_margin - q1_gp_margin
        margin_variation = (totals_next['SKU']['Sale Price'] - totals_current['SKU']['Sale Price']) - (totals_next['SKU']['Cost of Production per Unit'] - totals_current['SKU']['Cost of Production per Unit'])
        margin_price_effect = margin_variation * totals_current['SKU']['Units Sold']
        volume_variation=totals_next['SKU']['Units Sold']-totals_current['SKU']['Units Sold']
        margin_volume_effect = volume_variation * (totals_current['SKU']['Sale Price'] - totals_current['SKU']['Cost of Production per Unit'])
        margin_mix_effect = (q2_gp_margin - q1_gp_margin) - margin_price_effect - margin_volume_effect
        total_margin_change = margin_price_effect + margin_volume_effect + margin_mix_effect
        kpi_total = sum([revenue_price_effect, revenue_volume_effect, revenue_mix_effect]) * 100
        margin_growth_rate=((((totals_next['SKU']['Units Sold']*totals_next['SKU']['Sale Price'])-(totals_next['SKU']['Units Sold'] * totals_next['SKU']['Cost of Production per Unit']))-((totals_current['SKU']['Units Sold']*totals_current['SKU']['Sale Price'])-(totals_current['SKU']['Units Sold']*totals_current['SKU']['Cost of Production per Unit'])))/((totals_current['SKU']['Units Sold']*totals_current['SKU']['Sale Price'])-(totals_current['SKU']['Units Sold']*totals_current['SKU']['Cost of Production per Unit'])))*100
        margin_price_effect1=margin_price_effect/total_margin_change
        margin_volume_effect1=margin_volume_effect/total_margin_change
        margin_mix_effect1=margin_mix_effect/total_margin_change
        KPI=sum([margin_price_effect1,margin_volume_effect1,margin_mix_effect1])
        report_data.append([
        product, f"Total SKU ",
        round(totals_current['SKU']['Units Sold']),
        round(totals_current['SKU']['Sale Price']),
        round(totals_current['SKU']['Cost of Production per Unit']),
        "-", "-", "-",
        round(totals_next['SKU']['Units Sold']),
        round(totals_next['SKU']['Sale Price']),
        round(totals_next['SKU']['Cost of Production per Unit']),
        "-", "-", "-",
        f"{round(prior_total_sales):,.0f}",
        f"{round(current_total_sales):,.0f}",
        f"{price_variation:,.2f}",
        f"{round(price_effect):,.0f}",
        f"{round(volume_variation):,.0f}",
        f"{round(volume_effect):,.0f}",
        f"{round(mix_effect):,.0f}",
        f"{round(total_revenue_change):,.0f}",
        f"{round(prior_total_cost):,.0f}", # Add prior_total_cost here
        f"{round(current_total_cost):,.0f}",
        f"{round(q1_gp_margin):,.0f}",
        f"{round(q2_gp_margin):,.0f}",
        f"{round(gp_margin_change):,.0f}",
        f"{margin_variation:,.2f}",
        f"{round(margin_price_effect):,.0f}",
        f"{(volume_variation):,.2f}",
        f"{margin_volume_effect:,.2f}",
        f"{round(margin_mix_effect):,.0f}",
        f"{round(total_margin_change):,.0f}",
        f"{revenue_growth_rate:,.2f}%",
        f"{(revenue_price_effect*100):.3f}%",
        f"{(revenue_volume_effect*100):.0f}%",
        f"{effect:.3f}%",
        f"{kpi_total:,.3f}%",
        f"{margin_growth_rate:,.2f}%",
        f"{(margin_price_effect1 * 100):.1f}%",
        f"{round((margin_volume_effect1 * 100) if not pd.isna(margin_volume_effect1) else 0):.0f}%",
        f"{margin_mix_effect1:.2%}",
        f"{KPI:.2%}"

        ])
        prior_wo_sales = totals_current['WO']['Total Sale']
        current_wo_sales = totals_next['WO']['Total Sale']
        price_variation_wo = totals_next['WO']['Cost of Service Rate Billed'] - totals_current['WO']['Cost of Service Rate Billed']
        price_effect_wo = price_variation_wo * totals_current['WO']['Service Hours Billed']
        volume_variation_wo = totals_next['WO']['Service Hours Billed'] - totals_current['WO']['Service Hours Billed']
        volume_effect_wo = volume_variation_wo * totals_current['WO']['Cost of Service Rate Billed']
        mix_effect_wo = (current_wo_sales - prior_wo_sales) - price_effect_wo - volume_effect_wo
        total_revenue_change_wo = price_effect_wo + volume_effect_wo + mix_effect_wo
        prior_total_cost_wo = totals_current['WO']['Service Hours Billed'] * totals_current['WO']['Cost of Service Delivery Hour']
        current_total_cost_wo = totals_next['WO']['Service Hours Billed'] * totals_next['WO']['Cost of Service Delivery Hour']
        q1_gp_margin_wo = prior_wo_sales - prior_total_cost_wo
        q2_gp_margin_wo = current_wo_sales - current_total_cost_wo
        gp_margin_change_wo = q2_gp_margin_wo - q1_gp_margin_wo
        margin_variation_wo = (totals_next['WO']['Cost of Service Rate Billed'] - totals_current['WO']['Cost of Service Rate Billed']) - (totals_next['WO']['Cost of Service Delivery Hour'] - totals_current['WO']['Cost of Service Delivery Hour'])
        margin_price_effect_wo = margin_variation_wo * totals_current['WO']['Service Hours Billed']
        volume_variation_wo=totals_next['WO']['Service Hours Billed']-totals_current['WO']['Service Hours Billed']
        margin_volume_effect_wo = volume_variation_wo * (totals_current['WO']['Cost of Service Rate Billed'] - totals_current['WO']['Cost of Service Delivery Hour'])
        margin_mix_effect_wo = (q2_gp_margin_wo - q1_gp_margin_wo) - margin_price_effect_wo - margin_volume_effect_wo
        total_margin_change_wo = margin_price_effect_wo + margin_volume_effect_wo + margin_mix_effect_wo
        try:
            revenue_growth_rate_wo = ((current_wo_sales - prior_wo_sales) / prior_wo_sales) * 100
            revenue_price_effect_wo = price_effect_wo / total_revenue_change_wo
            revenue_volume_effect_wo = volume_effect_wo / total_revenue_change_wo
            revenue_mix_effect_wo = (mix_effect_wo / total_revenue_change_wo)
        except ZeroDivisionError:
            revenue_growth_rate_wo = 0
            revenue_price_effect_wo = 0
            revenue_volume_effect_wo = 0
            revenue_mix_effect_wo = 0

        kpi_total_wo = sum([revenue_price_effect_wo, revenue_volume_effect_wo, revenue_mix_effect_wo]) * 100
        margin_growth_rate_wo=((((totals_next['WO']['Service Hours Billed']*totals_next['WO']['Cost of Service Rate Billed'])-(totals_next['WO']['Service Hours Billed'] * totals_next['WO']['Cost of Service Delivery Hour']))-((totals_current['WO']['Service Hours Billed']*totals_current['WO']['Cost of Service Rate Billed'])-(totals_current['WO']['Service Hours Billed']*totals_current['WO']['Cost of Service Delivery Hour'])))/((totals_current['WO']['Service Hours Billed']*totals_current['WO']['Cost of Service Rate Billed'])-(totals_current['WO']['Service Hours Billed']*totals_current['WO']['Cost of Service Delivery Hour'])))*100
        margin_price_wo=margin_price_effect_wo/total_margin_change_wo
        margin_volume_wo=margin_volume_effect_wo/total_margin_change_wo
        margin_mix_wo=margin_mix_effect_wo/total_margin_change_wo
        kpi_wo=sum([margin_price_wo,margin_volume_wo,margin_mix_wo])
        # WO data
        report_data.append([
            product, f"Total WO ",
            "-", "-", "-",
            round(totals_current['WO']['Service Hours Billed']),
            round(totals_current['WO']['Cost of Service Rate Billed']),
            round(totals_current['WO']['Cost of Service Delivery Hour']),
            "-", "-", "-",
            round(totals_next['WO']['Service Hours Billed']),
            round(totals_next['WO']['Cost of Service Rate Billed']),
            round(totals_next['WO']['Cost of Service Delivery Hour']),
            f"{round(prior_wo_sales):,.0f}",
            f"{round(current_wo_sales):,.0f}",
            f"{price_variation_wo:,.2f}",
            f"{round(price_effect_wo):,.0f}",
            f"{round(volume_variation_wo):,.0f}",
            f"{round(volume_effect_wo):,.0f}",
            f"{round(mix_effect_wo):,.0f}",
            f"{round(total_revenue_change_wo):,.0f}",
            f"{round(prior_total_cost_wo):,.0f}",
            f"{round(current_total_cost_wo):,.0f}",
            f"{round(q1_gp_margin_wo):,.0f}",
            f"{round(q2_gp_margin_wo):,.0f}",
            f"{round(gp_margin_change_wo):,.0f}",
            f"{margin_variation_wo:,.2f}",
            f"{round(margin_price_effect_wo):,.0f}",
            f"{(volume_variation_wo):,.2f}",
            f"{margin_volume_effect_wo:,.2f}",
            f"{round(margin_mix_effect_wo):,.0f}",
            f"{round(total_margin_change_wo):,.0f}",
            f"{revenue_growth_rate_wo:,.5f}%",
            f"{(revenue_price_effect_wo*100):.3f}%",
            f"{(revenue_volume_effect_wo*100):.3f}%",
            f"{(revenue_mix_effect_wo*100):.3f}%",
            f"{kpi_total_wo:,.3f}%",
            f"{margin_growth_rate_wo:,.2f}%",
            f"{(margin_price_wo * 100):.1f}%",
            f"{round(margin_volume_wo * 100) if not pd.isna(margin_volume_wo) else 0:.0f}%",

            f"{margin_mix_wo:.2%}",
            f"{kpi_wo:.2%}"



        ])

    df_report = pd.DataFrame(report_data, columns=header)
    return df_report



def results(df):
    main = df[["Revenue Growth Rate ", "Margin Growth Rate"]]

    # Function to determine the category
    def categorize(row):
        rgr = float(row["Revenue Growth Rate "].replace(',', '').strip('%'))
        mgr = float(row["Margin Growth Rate"].replace(',', '').strip('%'))
        if rgr >= 15 and mgr >= 10:
            return "High Performers (Top-Right)"
        elif rgr >= 15 and 0 <= mgr < 10:
            return "Emerging Stars (Top-Middle)"
        elif rgr >= 15 and mgr < 0:
            return "Potential Leaders (Top-Left)"
        elif 0 <= rgr < 15 and mgr >= 10:
            return "Cash Cows (Middle-Right)"
        elif 0 <= rgr < 15 and 0 <= mgr < 10:
            return "Steady Performers (Center)"
        elif 0 <= rgr < 15 and mgr < 0:
            return "Undervalued Opportunities (Middle-Left)"
        elif rgr < 0 and mgr >= 10:
            return "Profit Drivers (Bottom-Right)"
        elif rgr < 0 and 0 <= mgr < 10:
            return "Question Marks (Bottom-Middle)"
        elif rgr < 0 and mgr < 0:
            return "Laggards (Bottom-Left)"
        else:
            return "Unclassified"

    # Apply the categorization function to each row, fixed indentation
    df["Category"] = df.apply(categorize, axis=1)
    # print(df.head(20).to_markdown(index=False, numalign="left", stralign="left"))
    return df # Return the modified DataFrame

# Assuming final_data is already defined and populated
def respones(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    combined_input = f"{prompt}"
    response = model.generate_content(combined_input)
    return response.text



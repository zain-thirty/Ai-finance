import pandas as pd
import google.generativeai as genai
import joblib
genai.configure(api_key='GOOGLE_API_KEY')
def load_data(file_path, sheet_name):
    data = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=4)
    return data
def cleaning_data(df):
    df=df.iloc[:,4:]
    row_index=0
    df.loc[row_index] = df.loc[row_index].fillna(method='ffill', axis=0)
    df.loc[row_index] = df.loc[row_index].astype('Int64')
    row_index=0
    df.loc[row_index] = df.loc[row_index].fillna(method='ffill', axis=0)
    df.loc[row_index] = df.loc[row_index].astype('Int64')
    row_index=1
    df.loc[row_index] = df.loc[row_index].fillna(method='ffill', axis=0)
    df1 = df.drop([3])
    df2=df1.iloc[2:,:]
    df2.columns=df2.iloc[0].values
    df2=df2.drop([2])
    df1 = df.drop([3])
    df2=df1.iloc[2:,:]
    df2.columns=df2.iloc[0].values
    df2=df2.drop([2])
    df2=df2.iloc[:,2:]
    df1=df1.iloc[:,2:]
    full_df=pd.DataFrame()
    for x in range(0,df2.shape[1],8):
        year=df1.iloc[0,x]
        month = df1.iloc[1,x]
        new_df=df2.iloc[:,x:x+8]
        new_df['Product Line']=df.iloc[4:,0]
        new_df['Type']=df.iloc[4:,1]
        new_df['Month']=month
        new_df['Year']=year
        new_df.set_index(["Year","Month",'Product Line', 'Type'], inplace=True)
        full_df=pd.concat([full_df,new_df])
    return full_df

def calculate_totals(year, month, product,full_df):
    """Calculate totals for a given product, year, and month."""
    sku_df = full_df.loc[(year, month, product)].loc[
        full_df.loc[(year, month, product)].index.get_level_values('Type').str.contains('SKU')
    ]
    # Calculate values for product with type SKU
    sku_units_sold = sku_df['Units Sold'].sum()
    sku_sale_price = sku_df['Sale Price'].mean()
    sku_units_made = sku_df['Units Made'].sum()
    sku_cost_of_production = sku_df['Cost of Production per Unit'].mean()
    sku_total_sale = sku_units_sold * sku_sale_price
    # Filter DataFrame for product with type WO
    wo_df = full_df.loc[(year, month, product)].loc[
        full_df.loc[(year, month, product)].index.get_level_values('Type').str.contains('WO')
    ]
    # Calculate values for product with type Wo
    wo_units_sold = wo_df['Units Sold'].sum()
    wo_sale_price = wo_df['Sale Price'].mean()
    wo_units_made = wo_df['Units Made'].sum()
    wo_cost_of_production = wo_df['Cost of Production per Unit'].mean()
    wo_service_hours_billed = wo_df['Service Hours Billed'].sum()
    wo_cost_of_service_rate_billed = wo_df['Cost of Service Rate Billed'].mean()
    wo_service_hours_worked = wo_df['Service Hours Worked'].sum()
    wo_cost_of_service_delivery_hour = wo_df['Cost of Service Delivery Hour'].mean()
    wo_total_sale= wo_service_hours_billed * wo_cost_of_service_rate_billed
    return {
        'Product': product,
        'SKU': {
            'Units Sold': sku_units_sold,
            'Sale Price': sku_sale_price,
            'Units Made': sku_units_made,
            'Cost of Production per Unit': sku_cost_of_production,
            'Total Sale': sku_total_sale,
        },
        'WO': {
            'Units Sold': wo_units_sold,
            'Sale Price': wo_sale_price,
            'Units Made': wo_units_made,
            'Cost of Production per Unit': wo_cost_of_production,
            'Service Hours Billed': wo_service_hours_billed,
            'Cost of Service Rate Billed': wo_cost_of_service_rate_billed,
            'Service Hours Worked': wo_service_hours_worked,
            'Cost of Service Delivery Hour': wo_cost_of_service_delivery_hour,
            'Total Sale': wo_total_sale,
        }
    }

def generate_report(year, month, year1, month1, product_lines,full_df):
    header = [
        "Product Line", "Type",
        f"Units Sold", f"Sale Price", f"Units Made",
        f"Cost Of Production per Unit",
        f"Service Hours Billed", f"Cost of Service Rate Billed",
        f"Service Hours Worked", f"Cost of Service Delivery Hour",
        f"Units Sold.1", f"Sale Price.1", f"Units Made.1",
        f"Cost Of Production per Unit.1",
        f"Service Hours Billed.1", f"Cost of Service Rate Billed.1",
        f"Service Hours Worked.1", f"Cost of Service Delivery Hour.1",
        "Prior Total Sales", "Current Total Sales", "Price Variation", "Price Effect",
        "Volume Variation", "Volume Effect", "Mix Effect", "Total Revenue Change",
         "Prior Total Cost ", "Current  Total Cost ", "Q1 GP Margin", "Q2 GP Margin",
        "GP Margin Change", "Margin Variation", "Margin Price Effect","Volume Variation.1",
        "Margin Volume Effect", "Margin Mix Effect", "Total Margin Change",
        "Revenue Growth Rate ", "Revenue Price Effect (%)", "Revenue Volume Effect (%)",
        "Revenue Mix Effect (%)", "KPI total ","Margin Growth Rate","Margin Price Effect (%)",
        "Margin Volume Effect (%)","Margin Mix Effect (%)","KPI total"
    ]
    report_data = []
    for product in product_lines:
        totals_current = calculate_totals(year, month, product,full_df)
        totals_next = calculate_totals(year1, month1, product,full_df)
        # SKU data
        prior_sku_sales = totals_current['SKU']['Total Sale']
        current_sku_sales = totals_next['SKU']['Units Sold'] * totals_next['SKU']['Sale Price']
        price_variation = totals_next['SKU']['Sale Price'] - totals_current['SKU']['Sale Price']
        price_effect = price_variation * totals_current['SKU']['Units Sold']
        volume_variation = totals_next['SKU']['Units Sold'] - totals_current['SKU']['Units Sold']
        volume_effect = volume_variation * totals_current['SKU']['Sale Price']
        volume_variation = totals_next['SKU']['Units Sold'] - totals_current['SKU']['Units Sold']
        volume_effect = volume_variation * totals_current['SKU']['Sale Price']
        mix_effect = (current_sku_sales - prior_sku_sales) - price_effect - volume_effect
        total_revenue_change = price_effect + volume_effect + mix_effect
        try:
            revenue_price_effect = price_effect / total_revenue_change
            revenue_volume_effect = volume_effect / total_revenue_change
            revenue_mix_effect =( mix_effect / total_revenue_change)
            revenue_growth_rate = ((current_sku_sales - prior_sku_sales) / prior_sku_sales) * 100
        except ZeroDivisionError:
            revenue_price_effect = 0
            revenue_volume_effect = 0
            revenue_mix_effect = 0
            revenue_growth_rate = 0
        effect=revenue_mix_effect*100
        prior_total_cost = totals_current['SKU']['Units Sold'] * totals_current['SKU']['Cost of Production per Unit']
        current_total_cost = totals_next['SKU']['Units Sold'] * totals_next['SKU']['Cost of Production per Unit']
        q1_gp_margin = prior_sku_sales - prior_total_cost
        q2_gp_margin = current_sku_sales - current_total_cost
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
            product, f"Total SKU {product[-1]}",
            round(totals_current['SKU']['Units Sold']),
            round(totals_current['SKU']['Sale Price']),
            round(totals_current['SKU']['Units Made']),
            round(totals_current['SKU']['Cost of Production per Unit']),
            "-", "-", "-", "-",
            round(totals_next['SKU']['Units Sold']),
            round(totals_next['SKU']['Sale Price']),
            round(totals_next['SKU']['Units Made']),
            round(totals_next['SKU']['Cost of Production per Unit']),
            "-", "-", "-", "-",
            f"{round(prior_sku_sales):,.0f}",
            f"{round(current_sku_sales):,.0f}",
            f"{price_variation:,.2f}",
            f"{round(price_effect):,.0f}",
            f"{round(volume_variation):,.0f}",
            f"{round(volume_effect):,.0f}",
            f"{round(mix_effect):,.0f}",
            f"{round(total_revenue_change):,.0f}",
            f"{round(prior_total_cost):,.0f}",
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
            f"{round(margin_volume_effect1 * 100):.0f}%",
            f"{margin_mix_effect1:.2%}",
            f"{KPI:.2%}"
        ])

        # WO data
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


        report_data.append([
            product, f"Total WO {product[-1]}",
            "-", "-", "-", "-",
            round(totals_current['WO']['Service Hours Billed']),
            round(totals_current['WO']['Cost of Service Rate Billed']),
            round(totals_current['WO']['Service Hours Worked']),
            round(totals_current['WO']['Cost of Service Delivery Hour']),
            "-", "-", "-", "-",
            round(totals_next['WO']['Service Hours Billed']),
            round(totals_next['WO']['Cost of Service Rate Billed']),
            round(totals_next['WO']['Service Hours Worked']),
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
            f"{round(margin_volume_wo * 100):.0f}%",
            f"{margin_mix_wo:.2%}",
            f"{kpi_wo:.2%}"
        ])
    df = pd.DataFrame(report_data, columns=header)
    return df

def results(df):
    main = df[["Revenue Growth Rate ", "Margin Growth Rate"]]

    # Function to determine the category
    def categorize(row):
        rgr = float(row["Revenue Growth Rate "].strip('%'))
        mgr = float(row["Margin Growth Rate"].strip('%'))
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



import pandas as pd
import numpy as np
import os

def calculate_mean_stiffness(csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return

    # 1. Load Data
    df = pd.read_csv(csv_path)
    
    # 2. Identify and Average Columns
    stiffness_cols = [f'C{i}{j}' for i in range(1, 7) for j in range(1, 7)]
    
    # Check for missing columns
    missing = [c for c in stiffness_cols if c not in df.columns]
    if missing:
        print(f"Error: Missing columns {missing}")
        return

    # Calculate the mean (this creates a Series with indices C11, C12...)
    mean_series = df[stiffness_cols].mean()
    
    # 3. Console Output (Clean Matrix Format for viewing)
    mean_matrix = mean_series.values.reshape(6, 6)
    print(f"\nMean Stiffness Matrix (Averaged over {len(df)} samples):")
    print("-" * 75)
    for row in mean_matrix:
        print("  ".join(f"{val:10.4f}" for val in row))
    print("-" * 75)
    
    # 4. Save to CSV (Single Row with Headers)
    output_path = os.path.join(os.path.dirname(csv_path), "Mean_Stiffness.csv")
    
    # Convert Series to a single-row DataFrame
    output_df = mean_series.to_frame().T 
    
    # Save with headers
    output_df.to_csv(output_path, index=False)
    
    print(f"Saved flattened mean matrix to: {output_path}")
    
    return mean_matrix

if __name__ == "__main__":
    # Example usage
    calculate_mean_stiffness("Volume_results.csv")
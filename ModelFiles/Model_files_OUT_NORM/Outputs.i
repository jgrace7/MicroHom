[Outputs]
  [./exodus_out]
    type = Exodus
    file_base = {{EXODUS_FILENAME}}
  [../]

  [./csv_out]
    type = CSV
    file_base = {{CSV_FILENAME}}
  [../]
[]

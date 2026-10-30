  [./G_{{PHASE}}]
    type = AnisoHeatConductionMaterial
    block = {{BLOCK}}
    thermal_conductivity = '{{G}} 0.0 0.0 0.0 {{G}} 0.0 0.0 0.0 0.0'
    specific_heat = 1.0
    temperature = u_z
  [../]
  [./G_{{PHASE}}]
    type = AnisoHeatConductionMaterial
    block = {{BLOCK}}
    thermal_conductivity = '{{Kxx}} {{Kxy}} {{Kxz}} {{Kyx}} {{Kyy}} {{Kyz}} {{Kzx}} {{Kzy}} {{Kzz}}'
    specific_heat = 1.0
    temperature = u_z
  [../]

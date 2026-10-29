  [./{{LABEL}}_E11]
    type = ParsedPostprocessor
    expression = 'int_strain_xx_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_strain_xx_{{PHASE}} volume_{{PHASE}}'
  [../]
  [./{{LABEL}}_E22]
    type = ParsedPostprocessor
    expression = 'int_strain_yy_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_strain_yy_{{PHASE}} volume_{{PHASE}}'
  [../]
  [./{{LABEL}}_E33]
    type = ConstantPostprocessor
    value = 0.0
  [../]
  [./{{LABEL}}_E12]
    type = ParsedPostprocessor
    expression = 'int_strain_xy_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_strain_xy_{{PHASE}} volume_{{PHASE}}'
  [../]
  [./{{LABEL}}_S11]
    type = ParsedPostprocessor
    expression = 'int_stress_xx_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_stress_xx_{{PHASE}} volume_{{PHASE}}'
  [../]
  [./{{LABEL}}_S22]  
    type = ParsedPostprocessor
    expression = 'int_stress_yy_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_stress_yy_{{PHASE}} volume_{{PHASE}}'
  [../]
  [./{{LABEL}}_S33]
    type = ConstantPostprocessor
    value = 0.0
  [../]
  [./{{LABEL}}_S12]
    type = ParsedPostprocessor
    expression = 'int_stress_xy_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_stress_xy_{{PHASE}} volume_{{PHASE}}'
  [../]
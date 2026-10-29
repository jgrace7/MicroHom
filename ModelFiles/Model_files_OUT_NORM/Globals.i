  [./int_{{VAR}}_global]
    type = ElementIntegralMaterialProperty
    mat_prop = {{VAR}}
    outputs = none
  [../]
  
  [./avg_{{VAR}}_global]
    type = ParsedPostprocessor
    expression = 'int_{{VAR}}_global / volume_global'
    pp_names = 'int_{{VAR}}_global volume_global'
  [../]

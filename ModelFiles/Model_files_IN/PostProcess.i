  [./int_{{VAR}}_{{PHASE}}]
    type = ElementIntegralMaterialProperty
    mat_prop = {{VAR}}
    block = '{{BLOCKS}}'
  [../]

  [./avg_{{VAR}}_{{PHASE}}]
    type = ParsedPostprocessor
    expression = 'int_{{VAR}}_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_{{VAR}}_{{PHASE}} volume_{{PHASE}}'
  [../]

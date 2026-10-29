  [./int_{{VAR}}_{{PHASE}}]
    type = ElementIntegralVariablePostprocessor
    variable = {{VAR}}
    block = '{{BLOCKS}}'
  [../]

  [./avg_{{VAR}}_{{PHASE}}]
    type = ParsedPostprocessor
    expression = 'int_{{VAR}}_{{PHASE}} / volume_{{PHASE}}'
    pp_names = 'int_{{VAR}}_{{PHASE}} volume_{{PHASE}}'
  [../]

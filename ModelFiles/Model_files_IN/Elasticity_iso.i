  [./elasticity_{{PHASE}}]
    type = ComputeIsotropicElasticityTensor
    block = {{BLOCK}}
    youngs_modulus = {{E}}
    poissons_ratio = {{NU}}
  [../]

#!/bin/bash

conda activate yammbs

# python remove_cosmetic_attributes.py            \
#     --input "../04_fit-forcefield/nor4/fb-fit/result/optimize/force-field.offxml"       \
#     --output "../openff-2.2.1-rc1.offxml"

# python remove_cosmetic_attributes.py            \
#     --input "../04_fit-forcefield/a27-half-k/fb-fit/result/optimize/force-field.offxml"       \
#     --output "openff-2.2.1-a27-half-k.offxml"


python remove_cosmetic_attributes.py            \
    --input "../04_fit-forcefield/a27-quarter-k/fb-fit/result/optimize/force-field.offxml"       \
    --output "openff-2.2.1-a27-quarter-k.offxml"

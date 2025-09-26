/**
 *
 *    Copyright (c) 2024-2025 Project CHIP Authors
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *        http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */

#include "thermostat-server.h"

#include <platform/internal/CHIPDeviceLayerInternal.h>

using namespace chip;
using namespace chip::app;
using namespace chip::app::Clusters;
using namespace chip::app::Clusters::Thermostat;
using namespace chip::app::Clusters::Thermostat::Attributes;
using namespace chip::app::Clusters::Thermostat::Structs;
using namespace chip::app::Clusters::Globals::Structs;
using namespace chip::Protocols::InteractionModel;

bool IsBuiltIn(const Structs::ScheduleStruct::DecodableType & schedule)
{
    return schedule.builtIn.ValueOr(false);
}

CHIP_ERROR ThermostatAttrAccess::AppendPendingSchedule(Thermostat::Delegate * delegate, const ScheduleStruct::DecodableType & newSchedule)
{
    ChipLogError(Zcl, "AppendPendingSchedule()");

    ScheduleStruct::Type schedule;

    if (newSchedule.scheduleHandle.IsNull())
    {
        if (IsBuiltIn(newSchedule))
        {
            return CHIP_IM_GLOBAL_STATUS(ConstraintError);
        }
        // Force to be false, if passed as null
        schedule.builtIn = DataModel::MakeNullable(false);
    }

    // PresetStructWithOwnedMembers preset = newPreset;
    // if (!IsValidPresetEntry(preset))
    // {
    //     return CHIP_IM_GLOBAL_STATUS(ConstraintError);
    // }

    // if (preset.GetPresetHandle().IsNull())
    // {
    //     if (IsBuiltIn(preset))
    //     {
    //         return CHIP_IM_GLOBAL_STATUS(ConstraintError);
    //     }
    //     // Force to be false, if passed as null
    //     preset.SetBuiltIn(false);
    // }
    // else
    // {
    //     // Per spec we need to check that:
    //     // (a) There is an existing non-pending preset with this handle.
    //     PresetStructWithOwnedMembers matchingPreset;
    //     if (!GetMatchingPresetInPresets(delegate, preset.GetPresetHandle().Value(), matchingPreset))
    //     {
    //         return CHIP_IM_GLOBAL_STATUS(NotFound);
    //     }

    //     // (b) There is no existing pending preset with this handle.
    //     if (CountPresetsInPendingListWithPresetHandle(delegate, preset.GetPresetHandle().Value()) > 0)
    //     {
    //         return CHIP_IM_GLOBAL_STATUS(ConstraintError);
    //     }

    //     const auto & presetBuiltIn         = preset.GetBuiltIn();
    //     const auto & matchingPresetBuiltIn = matchingPreset.GetBuiltIn();
    //     // (c)/(d) The built-in fields do not have a mismatch.
    //     if (presetBuiltIn.IsNull())
    //     {
    //         if (matchingPresetBuiltIn.IsNull())
    //         {
    //             // This really shouldn't happen; internal presets should alway have built-in set
    //             return CHIP_IM_GLOBAL_STATUS(InvalidInState);
    //         }
    //         preset.SetBuiltIn(matchingPresetBuiltIn.Value());
    //     }
    //     else
    //     {
    //         if (matchingPresetBuiltIn.IsNull())
    //         {
    //             // This really shouldn't happen; internal presets should alway have built-in set
    //             return CHIP_IM_GLOBAL_STATUS(InvalidInState);
    //         }
    //         if (presetBuiltIn.Value() != matchingPresetBuiltIn.Value())
    //         {
    //             return CHIP_IM_GLOBAL_STATUS(ConstraintError);
    //         }
    //     }
    // }

    // size_t maximumPresetCount         = delegate->GetNumberOfPresets();
    // size_t maximumPresetScenarioCount = 0;
    // if (MaximumPresetScenarioCount(delegate, preset.GetPresetScenario(), maximumPresetScenarioCount) != CHIP_NO_ERROR)
    // {
    //     return CHIP_IM_GLOBAL_STATUS(InvalidInState);
    // }

    // if (maximumPresetScenarioCount == 0)
    // {
    //     // This is not a supported preset scenario
    //     return CHIP_IM_GLOBAL_STATUS(ConstraintError);
    // }

    // if (preset.GetName().HasValue() && !PresetTypeSupportsNames(delegate, preset.GetPresetScenario()))
    // {
    //     return CHIP_IM_GLOBAL_STATUS(ConstraintError);
    // }

    // // Before adding this preset to the pending presets, if the expected length of the pending presets' list
    // // exceeds the total number of presets supported, return RESOURCE_EXHAUSTED. Note that the preset has not been appended yet.

    // // We're going to append this preset, so let's assume a count as though it had already been inserted
    // size_t presetCount         = 1;
    // size_t presetScenarioCount = 1;
    // for (uint8_t i = 0; true; i++)
    // {
    //     PresetStructWithOwnedMembers otherPreset;
    //     CHIP_ERROR err = delegate->GetPendingPresetAtIndex(i, otherPreset);

    //     if (err == CHIP_ERROR_PROVIDER_LIST_EXHAUSTED)
    //     {
    //         break;
    //     }
    //     if (err != CHIP_NO_ERROR)
    //     {
    //         return CHIP_IM_GLOBAL_STATUS(InvalidInState);
    //     }
    //     presetCount++;
    //     if (preset.GetPresetScenario() == otherPreset.GetPresetScenario())
    //     {
    //         presetScenarioCount++;
    //     }
    // }

    // if (presetCount > maximumPresetCount)
    // {
    //     ChipLogError(Zcl, "Preset count exceeded %u: %u ", static_cast<unsigned>(maximumPresetCount),
    //                  static_cast<unsigned>(presetCount));
    //     return CHIP_IM_GLOBAL_STATUS(ResourceExhausted);
    // }

    // if (presetScenarioCount > maximumPresetScenarioCount)
    // {
    //     ChipLogError(Zcl, "Preset scenario count exceeded %u: %u ", static_cast<unsigned>(maximumPresetScenarioCount),
    //                  static_cast<unsigned>(presetScenarioCount));
    //     return CHIP_IM_GLOBAL_STATUS(ResourceExhausted);
    // }

    schedule.builtIn    = newSchedule.builtIn;

    return delegate->AppendToPendingScheduleList(schedule);

    return CHIP_NO_ERROR;
}



Status ThermostatAttrAccess::PrecommitSchedules(EndpointId endpoint)
{
    ChipLogError(Zcl, "PrecommitSchedules()");

    auto delegate = GetDelegate(endpoint);

    if (delegate == nullptr)
    {
        ChipLogError(Zcl, "Delegate is null");
        return Status::InvalidInState;
    }

    CHIP_ERROR err = CHIP_NO_ERROR;

    for (uint8_t i = 0; true; i++)
    {
        ScheduleStruct::Type schedule;
        err = delegate->GetScheduleAtIndex(i, schedule);

        if (err == CHIP_ERROR_PROVIDER_LIST_EXHAUSTED)
        {
            break;
        }
    }



    return Status::Success;
}
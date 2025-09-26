#
#    Copyright (c) 2025 Project CHIP Authors
#    All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# See https://github.com/project-chip/connectedhomeip/blob/master/docs/testing/python.md#defining-the-ci-test-arguments
# for details about the block below.
#
# === BEGIN CI TEST ARGUMENTS ===
# test-runner-runs:
#   run1:
#     app: ${ALL_CLUSTERS_APP}
#     app-args: --discriminator 1234 --KVS kvs1 --trace-to json:${TRACE_APP}.json
#     script-args: >
#       --storage-path admin_storage.json
#       --commissioning-method on-network
#       --discriminator 1234
#       --passcode 20202021
#       --endpoint 1
#       --trace-to json:${TRACE_TEST_JSON}.json
#       --trace-to perfetto:${TRACE_TEST_PERFETTO}.perfetto
#     factory-reset: true
#     quiet: true
# === END CI TEST ARGUMENTS ===

import copy
import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from mobly import asserts

import matter.clusters as Clusters
from matter import ChipDeviceCtrl  # Needed before matter.FabricAdmin
from matter.clusters import Globals
from matter.clusters.Types import NullValue
from matter.interaction_model import InteractionModelError, Status
from matter.testing.matter_testing import MatterBaseTest, TestStep, async_test_body, default_matter_test_main

logger = logging.getLogger(__name__)

cluster = Clusters.Thermostat

class TC_TSTAT_4_4(MatterBaseTest):

    def check_returned_schedules(self, sent_schedules: list, returned_schedules: list):
        asserts.assert_true(len(sent_schedules) == len(returned_schedules), "Returned returned_schedules are a different length than sent returned_schedules")
        for i, sent_preset in enumerate(sent_schedules):
            returned_preset = returned_schedules[i]
            if sent_preset.presetHandle is NullValue:
                sent_preset = copy.copy(sent_preset)
                sent_preset.presetHandle = returned_preset.presetHandle
            if sent_preset.builtIn is NullValue:
                sent_preset.builtIn = returned_preset.builtIn
            asserts.assert_equal(sent_preset, returned_preset,
                                 "Returned schedule is not the same as sent schedule")

    def check_atomic_response(self, response: object, 
                              expected_status: Status = Status.Success,
                              expected_overall_status: Status = Status.Success,
                              expected_schedules_status: Status = Status.Success,
                              expected_timeout: int = None):
        asserts.assert_equal(expected_status, Status.Success, "We expected we had a valid response")
        asserts.assert_equal(response.statusCode, expected_overall_status, "Response should have the right overall status")
        found_schedules_status = False
        for attrStatus in response.attributeStatus:
            if attrStatus.attributeID == cluster.Attributes.Schedules.attribute_id:
                asserts.assert_equal(attrStatus.statusCode, expected_schedules_status,
                                     "Schedules attribute should have the right status")
                found_schedules_status = True
        if expected_timeout is not None:
            asserts.assert_equal(response.timeout, expected_timeout,
                                 "Timeout should have the right value")
        if expected_schedules_status is not None:
            asserts.assert_true(found_schedules_status, "Schedules attribute should have a status")
            asserts.assert_equal(attrStatus.statusCode, expected_schedules_status,
                                 "Schedules attribute should have the right status")

        logger.info(f"check_atomic_response returned successfully")    

    def make_schedule(self, systemMode, scheduleHandle=NullValue, builtIn=True):
        schedule = cluster.Structs.ScheduleStruct(scheduleHandle=scheduleHandle, systemMode=systemMode, transitions=[], name=None, presetHandle=None, builtIn=builtIn)
        #if self.check_pics("TSTAT.S.F00"):
        #    preset.heatingSetpoint = heatSetpoint
        #if self.check_pics("TSTAT.S.F01"):
        #    preset.coolingSetpoint = coolSetpoint
        #if name is not None:
        #    preset.name = name
        return schedule

    async def write_schedules(self,
                              endpoint,
                              schedules,
                              dev_ctrl: ChipDeviceCtrl = None,
                              expected_status: Status = Status.Success) -> Status:
        if dev_ctrl is None:
            dev_ctrl = self.default_controller
        result = await dev_ctrl.WriteAttribute(self.dut_node_id, [(endpoint, cluster.Attributes.Schedules(schedules))])
        status = result[0].Status
        asserts.assert_equal(status, expected_status, f"Schedules write returned {status.name}; expected {expected_status.name}")
        return status

    async def send_atomic_request_begin_command(self,
                                                dev_ctrl: ChipDeviceCtrl = None,
                                                endpoint: int = 1,
                                                timeout: int = 30000,
                                                expected_status: Status = Status.Success,
                                                expected_overall_status: Status = Status.Success,
                                                expected_schedules_status: Status = Status.Success,
                                                expected_timeout: int = None):
        try:
            response = await self.send_single_cmd(cmd=cluster.Commands.AtomicRequest(requestType=Globals.Enums.AtomicRequestTypeEnum.kBeginWrite,
                                                                                     attributeRequests=[
                                                                                         cluster.Attributes.Schedules.attribute_id],
                                                                                     timeout=timeout),
                                                  dev_ctrl=dev_ctrl,
                                                  endpoint=endpoint)
            self.check_atomic_response(response, expected_status, 
                                       expected_overall_status,
                                       expected_schedules_status, expected_timeout)

        except InteractionModelError as e:
            asserts.assert_equal(e.status, expected_status, "Atomic request begin: Unexpected error returned")

    async def send_atomic_request_rollback_command(self,
                                                   dev_ctrl: ChipDeviceCtrl = None,
                                                   endpoint: int = 1,
                                                   expected_status: Status = Status.Success,
                                                   expected_overall_status: Status = Status.Success,
                                                   expected_schedules_status: Status = Status.Success):
        try:
            response = await self.send_single_cmd(cmd=cluster.Commands.AtomicRequest(requestType=Globals.Enums.AtomicRequestTypeEnum.kRollbackWrite,
                                                                                     attributeRequests=[cluster.Attributes.Schedules.attribute_id]),
                                                  dev_ctrl=dev_ctrl,
                                                  endpoint=endpoint)
            self.check_atomic_response(response, expected_status, expected_overall_status, expected_schedules_status)

        except InteractionModelError as e:
            asserts.assert_equal(e.status, expected_status, "Unexpected error returned")

    def desc_TC_TSTAT_4_4(self) -> str:
        """Returns a description of this test"""
        return "3.1.5 [TC-TSTAT-4-4] This test case verifies that the DUT can respond to Matter schedule commands."

    def pics_TC_TSTAT_4_4(self):
        """ This function returns a list of PICS for this test case that must be True for the test to be run"""
        return ["TSTAT.S", "TSTAT.S.F07"]

    def steps_TC_TSTAT_4_4(self) -> list[TestStep]:
        steps = [
            TestStep("1", "Commissioning, already done",
                     is_commissioning=True),
            TestStep("2", "TH writes to the Schedules attribute without calling the AtomicRequest command",
                     "Verify that the write request returns INVALID_IN_STATE error since the client didn't send a request to edit the schedules by calling AtomicRequest command."),                     
            TestStep("3", "TH writes to the Schedules attribute after calling the AtomicRequest begin command and then calls AtomicRequest rollback",
                     "Verify that the Schedules attribute was not updated since AtomicRequest rollback command was called."),
            # TestStep("4", "TH writes to the Schedules attribute after calling the AtomicRequest begin command and calls AtomicRequest commit",
            #          "Verify that the Schedules attribute was updated with new schedules."),
            # TestStep("5", "TH reads the ScheduleTypes attribute and saves it in a SupportedScheduleTypes variable.",
            #          "Verify that the read returned a list of schedule types with count >=2."),
        ]

        return steps

    @ async_test_body
    async def test_TC_TSTAT_4_4(self):
        # TODO Why is the endpoint 0?
        endpoint = 1 # self.get_endpoint()

        logger.info(f"Endpoint: {endpoint}")

        self.step("1")
        # Commission DUT - already done

        self.step("2")
        #if self.pics_guard(self.check_pics("TSTAT.S.F07")):
        # Read the numberOfPresets supported.
        numberOfSchedulesSupported = await self.read_single_attribute_check_success(endpoint=endpoint, cluster=cluster, attribute=cluster.Attributes.NumberOfSchedules)

        # Read the ScheduleTypes to get the schedule scenarios supported by the Thermostat.
        scheduleTypes = await self.read_single_attribute_check_success(endpoint=endpoint, cluster=cluster, attribute=cluster.Attributes.ScheduleTypes)
        logger.info(f"Rx'd Schedule Types: {scheduleTypes}")

        current_schedules = await self.read_single_attribute_check_success(endpoint=endpoint, cluster=cluster, attribute=cluster.Attributes.Schedules)
        logger.info(f"Rx'd Schedules: {current_schedules}")

        scheduleCounts = len(current_schedules)

        # Write to the presets attribute without calling AtomicRequest command
        await self.write_schedules(endpoint=endpoint, schedules=current_schedules, expected_status=Status.InvalidInState)

        self.step("3")
        #if self.pics_guard(self.check_pics("TSTAT.S.F08") and self.check_pics("TSTAT.S.A0050") and self.check_pics("TSTAT.S.Cfe.Rsp")):

        #availableMode = self.get_available_scenario(presetTypes=presetTypes, presetScenarioCounts=presetScenarioCounts)

        #if availableScenario is not None and len(current_presets) < numberOfPresetsSupported:

        test_schedules = copy.deepcopy(current_schedules)
        # for schedule in test_schedules:
        #     schedule.builtIn = NullValue

        #test_schedules.append(self.make_schedule(Clusters.Objects.Thermostat.Enums.SystemModeEnum.kHeat))

        await self.send_atomic_request_begin_command()

        logger.info(f"Successfully sent beginWrite atomic request")

        # Write to the presets attribute after calling AtomicRequest command
        status = await self.write_schedules(endpoint=1, schedules=test_schedules)
        #status_ok = (status == Status.Success)
        #asserts.assert_true(status_ok, "Schedules write did not return Success as expected")

        # Read the schedules attribute and verify it was updated by the write
        saved_schedules = await self.read_single_attribute_check_success(endpoint=endpoint, cluster=cluster, attribute=cluster.Attributes.Schedules)
        logger.info(f"Rx'd Schedules: {saved_schedules}")
        self.check_returned_schedules(test_schedules, saved_schedules)

        await self.send_atomic_request_rollback_command()

        # Read the presets attribute and verify it has been properly rolled back
        schedules = await self.read_single_attribute_check_success(endpoint=endpoint, cluster=cluster, attribute=cluster.Attributes.Schedules)
        asserts.assert_equal(schedules, current_schedules, "Schedules were updated which is not expected")
    # else:
    #     logger.info(
    #         "Couldn't run test step 3 since there was no available preset scenario to append")

        # self.step("5")
        # #if self.pics_guard(self.check_pics("TSTAT.S.F0a")):
        #     # TH reads the ScheduleTypes attribute and saves it in a SupportedScheduleTypes variable.
        # supported_schedule_types = await self.read_single_attribute_check_success(endpoint=1, cluster=cluster, attribute=cluster.Attributes.ScheduleTypes)
        # logger.info(f"Supported Schedule Types: {supported_schedule_types}")

        # # Verify that the read returned a list of schedule types with count >=2.
        # asserts.assert_greater_equal(len(supported_schedule_types), 2)

if __name__ == "__main__":
    default_matter_test_main()

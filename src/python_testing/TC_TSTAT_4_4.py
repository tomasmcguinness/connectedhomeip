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

import asyncio
import logging
import random
from datetime import datetime, timedelta, timezone

from mobly import asserts

import matter.clusters as Clusters
from matter import ChipDeviceCtrl  # Needed before matter.FabricAdmin
from matter.interaction_model import InteractionModelError, Status
from matter.testing.matter_testing import MatterBaseTest, TestStep, async_test_body, default_matter_test_main

logger = logging.getLogger(__name__)

cluster = Clusters.Thermostat

class TC_TSTAT_4_4(MatterBaseTest):

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
            TestStep("3", "TH reads the ScheduleTypes attribute and saves it in a SupportedScheduleTypes variable.",
                     "Verify that the read returned a list of schedule types with count >=2."),
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

        # Write to the presets attribute without calling AtomicRequest command
        await self.write_schedules(endpoint=endpoint, schedules=current_schedules, expected_status=Status.InvalidInState)

        self.step("3")
        #if self.pics_guard(self.check_pics("TSTAT.S.F0a")):
            # TH reads the ScheduleTypes attribute and saves it in a SupportedScheduleTypes variable.
        supported_schedule_types = await self.read_single_attribute_check_success(endpoint=1, cluster=cluster, attribute=cluster.Attributes.ScheduleTypes)
        logger.info(f"Supported Schedule Types: {supported_schedule_types}")

        # Verify that the read returned a list of schedule types with count >=2.
        asserts.assert_greater_equal(len(supported_schedule_types), 2)

if __name__ == "__main__":
    default_matter_test_main()

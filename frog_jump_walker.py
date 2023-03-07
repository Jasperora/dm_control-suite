# Copyright 2017 The dm_control Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Frog Jump Planar Walker Domain."""

from __future__ import absolute_import, division, print_function

import collections

from dm_control import mujoco
from dm_control.rl import control
from dm_control.suite.utils import randomizers
from dm_control.utils import containers, rewards

from . import base, common
import numpy as np

# wandb
import wandb

_DEFAULT_TIME_LIMIT = 25
_CONTROL_TIMESTEP = 0.025

# Minimal height of torso over foot above which stand reward is 1.
_STAND_HEIGHT = 1.2

# Horizontal speeds (meters/second) above which move reward is 1.
_WALK_SPEED = 1
_RUN_SPEED = 8


SUITE = containers.TaggedTasks()


def get_model_and_assets():
  """Returns a tuple containing the model XML string and a dict of assets."""
  return common.read_model('walker.xml'), common.ASSETS


@SUITE.add("benchmarking")
def vel_1(
    time_limit=_DEFAULT_TIME_LIMIT,
    xml_file_id=None,
    random=None,
    environment_kwargs=None,
):
    """Returns the Stand task."""
    physics = Physics.from_xml_string(*get_model_and_assets())
    task = FrogJumpPlanarWalker(x_vel_limit=1, random=random)
    environment_kwargs = environment_kwargs or {}
    return control.Environment(
        physics,
        task,
        time_limit=time_limit,
        control_timestep=_CONTROL_TIMESTEP,
        **environment_kwargs,
    )


@SUITE.add("benchmarking")
def vel_2(
    time_limit=_DEFAULT_TIME_LIMIT,
    xml_file_id=None,
    random=None,
    environment_kwargs=None,
):
    """Returns the Walk task."""
    physics = Physics.from_xml_string(*get_model_and_assets())
    task = FrogJumpPlanarWalker(x_vel_limit=2, random=random)
    environment_kwargs = environment_kwargs or {}
    return control.Environment(
        physics,
        task,
        time_limit=time_limit,
        control_timestep=_CONTROL_TIMESTEP,
        **environment_kwargs,
    )

@SUITE.add("benchmarking")
def vel_3(
    time_limit=_DEFAULT_TIME_LIMIT,
    xml_file_id=None,
    random=None,
    environment_kwargs=None,
):
    """Returns the Run task."""
    physics = Physics.from_xml_string(*get_model_and_assets())
    task = FrogJumpPlanarWalker(x_vel_limit=3, random=random)
    environment_kwargs = environment_kwargs or {}
    return control.Environment(
        physics,
        task,
        time_limit=time_limit,
        control_timestep=_CONTROL_TIMESTEP,
        **environment_kwargs,
    )

@SUITE.add("benchmarking")
def vel_4(
    time_limit=_DEFAULT_TIME_LIMIT,
    xml_file_id=None,
    random=None,
    environment_kwargs=None,
):
    """Returns the Run task."""
    physics = Physics.from_xml_string(*get_model_and_assets())
    task = FrogJumpPlanarWalker(x_vel_limit=4, random=random)
    environment_kwargs = environment_kwargs or {}
    return control.Environment(
        physics,
        task,
        time_limit=time_limit,
        control_timestep=_CONTROL_TIMESTEP,
        **environment_kwargs,
    )

@SUITE.add("benchmarking")
def vel_5(
    time_limit=_DEFAULT_TIME_LIMIT,
    xml_file_id=None,
    random=None,
    environment_kwargs=None,
):
    """Returns the Run task."""
    physics = Physics.from_xml_string(*get_model_and_assets())
    task = FrogJumpPlanarWalker(x_vel_limit=5, random=random)
    environment_kwargs = environment_kwargs or {}
    return control.Environment(
        physics,
        task,
        time_limit=time_limit,
        control_timestep=_CONTROL_TIMESTEP,
        **environment_kwargs,
    )

@SUITE.add("benchmarking")
def vel_6(
    time_limit=_DEFAULT_TIME_LIMIT,
    xml_file_id=None,
    random=None,
    environment_kwargs=None,
):
    """Returns the Run task."""
    physics = Physics.from_xml_string(*get_model_and_assets())
    task = FrogJumpPlanarWalker(x_vel_limit=6, random=random)
    environment_kwargs = environment_kwargs or {}
    return control.Environment(
        physics,
        task,
        time_limit=time_limit,
        control_timestep=_CONTROL_TIMESTEP,
        **environment_kwargs,
    )


class Physics(mujoco.Physics):
    """Physics simulation with additional features for the Walker domain."""

    def torso_upright(self):
        """Returns projection from z-axes of torso to the z-axes of world."""
        return self.named.data.xmat["torso", "zz"]

    def torso_height(self):
        """Returns the height of the torso."""
        return self.named.data.xpos["torso", "z"]

    def horizontal_velocity(self):
        """Returns the horizontal velocity of the center-of-mass."""
        return self.named.data.sensordata["torso_subtreelinvel"][0]

    def orientations(self):
        """Returns planar orientations of all bodies."""
        return self.named.data.xmat[1:, ["xx", "xz"]].ravel()


class FrogJumpPlanarWalker(base.Task):
    """A planar walker task."""

    def __init__(self, x_vel_limit, random=None):
        """Initializes an instance of `PlanarWalker`.
        Args:
          move_speed: A float. If this value is zero, reward is given simply for
            standing up. Otherwise this specifies a target horizontal velocity for
            the walking task.
          random: Optional, either a `numpy.random.RandomState` instance, an
            integer seed for creating a new `RandomState`, or None to select a seed
            automatically (default).
        """
        self._x_vel_limit = x_vel_limit
        super(FrogJumpPlanarWalker, self).__init__(random=random)
        self.random_seed = random
        self._x_vel_reward = 1
        self._alive_reward = 1
        self._angle_reward = 0.1
        self._ctrl_penalty = 1e-3
        self._foot_penalty = 0.01
        self._height_reward = 1
        self._foot_diff_penalty = 1
        self._thigh_diff_penalty = 1
        self._leg_diff_penalty = 1
        # self._jump_reward = 3
        self._not_jump_penalty = 2
        self._height_diff_reward = 1
        self._thigh_foot_reward = 2
        self._squat_reward = 4

        self._min_height = 0.1

        self.init_qpos = None
        self.init_named_geom_xpos = None
        self.qpos_before = None
        self.qpos_after = None
        self.named_geom_xpos_before = None
        self.named_geom_xpos_after = None
        self.action = None
        self.jump = False
        

    def initialize_episode(self, physics):
        """Sets the state of the environment at the start of each episode.
        In 'standing' mode, use initial orientation and small velocities.
        In 'random' mode, randomize joint angles and let fall to the floor.
        Args:
          physics: An instance of `Physics`.
        """
        # randomizers.randomize_limited_and_rotational_joints(physics, self.random)
        if self.init_qpos is None:
            self.init_qpos = physics.data.qpos.copy()
            self.init_qvel = physics.data.qvel.copy()
        if self.init_named_geom_xpos is None:
            self.init_named_geom_xpos = physics.named.data.geom_xpos
        np.random.seed(self.random_seed)
        physics.data.qpos = self.init_qpos.copy() + (np.random.random(self.init_qpos.shape)-.5)*0.001
        physics.data.qvel = self.init_qvel.copy() + (np.random.random(self.init_qvel.shape)-.5)*0.001
        super(FrogJumpPlanarWalker, self).initialize_episode(physics)

    def get_observation(self, physics):
        """Returns an observation of body orientations, height and velocites."""
        obs = collections.OrderedDict()
        obs["orientations"] = physics.orientations()
        obs["height"] = physics.torso_height()
        obs["velocity"] = physics.velocity()
        return obs

    def before_step(self, action, physics):
        """Sets the control signal for the actuators to values in `action`."""
        # Support legacy internal code.
        action = getattr(action, "continuous_actions", action)
        physics.set_control(action)
        self.action = action.copy()
        self.qpos_before = physics.data.qpos.copy()
        self.named_geom_xpos_before = physics.named.data.geom_xpos

    def after_step(self, physics):
        """Modifies colors according to the reward."""
        if self._visualize_reward:
            # reward = np.clip(self.get_reward(physics), 0.0, 1.0)
            reward = self.get_reward(physics)
            # _set_reward_colors(physics, reward)
        self.qpos_after = physics.data.qpos.copy()
        self.named_geom_xpos_after = physics.named.data.geom_xpos
        
    @property
    def is_healthy(self):
        z, angle = self.state_after[0], self.state_after[2]

        min_z, max_z = self._healthy_z_range
        min_angle, max_angle = self._healthy_angle_range

        healthy_z = min_z < z < max_z
        healthy_angle = min_angle < angle < max_angle
        is_healthy = healthy_z and healthy_angle

        return is_healthy

    def get_termination(self, physics):
        height = physics.named.data.geom_xpos["torso","z"]
        terminated = height < self._min_height
        if terminated:
            return 0.

    def get_reward(self, physics):
        """Returns a reward to the agent."""
        if self.qpos_before is None:
            qpos_before = self.init_qpos
        else:
            qpos_before = self.qpos_before
        if self.named_geom_xpos_before is None:
            named_geom_xpos_before = self.init_named_geom_xpos
        else:
            named_geom_xpos_before = self.named_geom_xpos_before

        right_foot_before = named_geom_xpos_before["right_foot","x"]
        left_foot_before = named_geom_xpos_before["left_foot","x"]
        height_before = named_geom_xpos_before["torso","z"]

        if self.qpos_after is None:
            qpos_after = qpos_before
        else:
            qpos_after = self.qpos_after
        if self.named_geom_xpos_after is None:
            named_geom_xpos_after = named_geom_xpos_before
        else:
            named_geom_xpos_after = self.named_geom_xpos_after

        right_foot_after = named_geom_xpos_after["right_foot","x"]
        left_foot_after = named_geom_xpos_after["left_foot","x"]

        height = named_geom_xpos_after["torso","z"]
        angle = physics.data.qpos[2]
        delta_h = physics.named.data.geom_xpos["torso","z"] - max(physics.named.data.geom_xpos["right_foot","z"], physics.named.data.geom_xpos["left_foot","z"])
        nz = np.cos(angle)
        x_vel = physics.horizontal_velocity()
        x_vel = self._x_vel_limit - abs(x_vel - self._x_vel_limit)
        right_foot_vel = abs(right_foot_after - right_foot_before) / _CONTROL_TIMESTEP
        left_foot_vel = abs(left_foot_after - left_foot_before) / _CONTROL_TIMESTEP
        leg_diff = abs(physics.named.data.geom_xpos["right_leg","x"]-physics.named.data.geom_xpos["left_leg","x"]) + \
            abs(physics.named.data.geom_xpos["right_leg","z"]-physics.named.data.geom_xpos["left_leg","z"])
        foot_diff = abs(physics.named.data.geom_xpos["right_foot","x"]-physics.named.data.geom_xpos["left_foot","x"]) + \
            abs(physics.named.data.geom_xpos["right_foot","z"]-physics.named.data.geom_xpos["left_foot","z"])
        thigh_diff = abs(physics.named.data.geom_xpos["right_thigh","x"]-physics.named.data.geom_xpos["left_thigh","x"]) + \
            abs(physics.named.data.geom_xpos["right_thigh","z"]-physics.named.data.geom_xpos["left_thigh","z"])
        height_diff = abs(height - height_before)

        # reward
        x_vel_reward = self._x_vel_reward * x_vel
        angle_reward = self._angle_reward * nz
        height_reward = self._height_reward * min(physics.named.data.geom_xpos["right_foot","z"],physics.named.data.geom_xpos["left_foot","z"])
        if self.action is None:
            ctrl_penalty = 0
        else:
            ctrl_penalty = -self._ctrl_penalty * np.sum(np.square(self.action))
        alive_reward = self._alive_reward
        foot_penalty = -self._foot_penalty * (right_foot_vel + left_foot_vel)
        leg_diff_penalty = -self._leg_diff_penalty * leg_diff
        foot_diff_penalty = -self._foot_diff_penalty * foot_diff
        thigh_diff_penalty = -self._thigh_diff_penalty * thigh_diff
        height_diff_reward = self._height_diff_reward * height_diff
        # if physics.named.data.geom_xpos["torso","z"] > 1.4 and physics.named.data.geom_xpos["right_foot","z"] > 0.35 and \
        #     physics.named.data.geom_xpos["left_foot","z"] > 0.35:
            # jump_reward = self._jump_reward * physics.named.data.geom_xpos["torso","z"]
        # else:
        #     jump_reward = 0

        not_jump_penalty = -self._not_jump_penalty * abs(1 - min(physics.named.data.geom_xpos["right_foot","z"], physics.named.data.geom_xpos["left_foot","z"]))

        if physics.named.data.geom_xpos["right_thigh","z"] > physics.named.data.geom_xpos["right_foot","z"] and \
            physics.named.data.geom_xpos["left_thigh","z"] > physics.named.data.geom_xpos["left_foot","z"]:
            thigh_foot_reward = self._thigh_foot_reward
        else:
            thigh_foot_reward = 0
        
        if (physics.named.data.geom_xpos["torso","z"] > 1.35 and physics.named.data.geom_xpos["right_foot","z"] > 0.35 and \
            physics.named.data.geom_xpos["left_foot","z"] > 0.35) or self.jump==True:
            self.jump = True
        else:
            self.jump = False

        if self.jump and physics.named.data.geom_xpos["torso","z"] < 0.7:
            squat_reward = self._squat_reward
            self.jump = False
        else:
            squat_reward = 0      

        reward = x_vel_reward + angle_reward + height_reward + not_jump_penalty + \
                ctrl_penalty + alive_reward + foot_penalty + leg_diff_penalty + foot_diff_penalty + \
                thigh_diff_penalty + height_diff_reward + thigh_foot_reward + squat_reward
                
        info = {
        #     "x_vel_reward": x_vel_reward,
        #     "angle_reward": angle_reward,
        #     "height_reward": height_reward,
        #     "ctrl_penalty": ctrl_penalty,
        #     "alive_reward": alive_reward,
        #     "foot_penalty": foot_penalty,
        #     "reward": reward,
        #     "delta_h_mean": delta_h,
        #     "nz_mean": nz,
        #     "x_vel_mean": (x_after - x_before) / _CONTROL_TIMESTEP,
            "height_mean": height,
            "left_foot_z": physics.named.data.geom_xpos["left_foot","z"],
            "right_foot_z": physics.named.data.geom_xpos["right_foot","z"],
        }

        # wandb.log(info)

        return reward
# -*- coding: utf-8 -*-
"""
Adding a model wrapper for using asynchronous model API
"""
# pylint: disable=R1710
from typing import Optional, Any
from http import HTTPStatus
import asyncio
from dashscope.aigc.generation import AioGeneration
from agentscope.models import DashScopeChatWrapper, ModelResponse


class AsyncDashScopeChatWrapper(DashScopeChatWrapper):
    """
    Model wrapper for using async dashscope API
    """

    model_type: str = "async_dashscope_chat"

    def __call__(  # pylint: disable=W0222
        self,
        messages: list,
        stream: Optional[bool] = False,
        tools: Optional[list[dict]] = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        This is a specialized wrapper for the async dashscope API.
        Most of the parameters are the same as the sync version.

        Args:
            messages (`list`):
                A list of messages to process.
            stream (`Optional[bool]`, default `None`):
                The stream flag to control the response format, which will
                overwrite the stream flag in the constructor.
            **kwargs (`Any`):
                The keyword arguments to DashScope chat completions API,
                e.g. `temperature`, `max_tokens`, `top_p`, etc. Please
                refer to
                https://help.aliyun.com/zh/dashscope/developer-reference/api-details
                for more detailed arguments.

        Returns:
            `ModelResponse`:
                A response object with the response text in text field, and
                the raw response in raw field. If stream is True, the response
                will be a generator in the `stream` field.

        Note:
            `parse_func`, `fault_handler` and `max_retries` are reserved for
            `_response_parse_decorator` to parse and check the response
            generated by model wrapper. Their usages are listed as follows:
                - `parse_func` is a callable function used to parse and check
                the response generated by the model, which takes the response
                as input.
                - `max_retries` is the maximum number of retries when the
                `parse_func` raise an exception.
                - `fault_handler` is a callable function which is called
                when the response generated by the model is invalid after
                `max_retries` retries.
            The rule of roles in messages for DashScope is very rigid,
            for more details, please refer to
            https://help.aliyun.com/zh/dashscope/developer-reference/api-details
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        if stream:
            async_gen = loop.run_until_complete(
                self.async_call(messages, stream, **kwargs),
            )
            try:
                while True:
                    response = loop.run_until_complete(async_gen.__anext__())
                    yield response
            except StopAsyncIteration as exc:
                print("Asynchronous iteration completed.", exc)
            finally:
                loop.close()
        else:
            return loop.run_until_complete(
                self.async_call(messages, stream, **kwargs),
            )

    async def async_call(
        self,
        messages: list,
        stream: Optional[bool] = False,
        **kwargs: Any,
    ) -> ModelResponse:
        """using async model api"""
        # step1: prepare keyword arguments
        kwargs = {**self.generate_args, **kwargs}

        # step2: checking messages
        if not isinstance(messages, list):
            raise ValueError(
                "Dashscope `messages` field expected type `list`, "
                f"got `{type(messages)}` instead.",
            )
        if not all("role" in msg and "content" in msg for msg in messages):
            raise ValueError(
                "Each message in the 'messages' list must contain a 'role' "
                "and 'content' key for DashScope API.",
            )

        # step3: forward to generate response

        kwargs.update(
            {
                "model": self.model_name,
                "messages": messages,
                # Set the result to be "message" format.
                "result_format": "message",
            },
        )

        # Switch to the incremental_output mode
        if stream:
            kwargs["incremental_output"] = True
            kwargs["stream"] = stream
        response = await AioGeneration.call(**kwargs)

        def handle_error(response: Any) -> None:
            if response.status_code != HTTPStatus.OK:
                error_msg = (
                    f"Request id: {response.request_id},\n"
                    f"Status code: {response.status_code},\n"
                    f"Error code: {response.code},\n"
                    f"Error message: {response.message}."
                )
                raise RuntimeError(error_msg)

        if stream:

            async def async_generator() -> Any:
                text = ""
                async for chunk in response:
                    handle_error(chunk)
                    text += chunk.output["choices"][0]["message"]["content"]
                    yield ModelResponse(text=text, raw=chunk)

            return async_generator()

        else:
            handle_error(response)
            return ModelResponse(
                text=response.output["choices"][0]["message"]["content"],
                raw=response,
            )

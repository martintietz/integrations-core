# (C) Datadog, Inc. 2021-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

def get_base_disk_usage_72(timeout):
    return {
        'name': 'base_disk_usage_72',
        'query': {
            'text': (
                # Use DISTINCT because one serial number can have multiple lines with different RESOURCE NAMEs,
                # but we only want one metric per disk for disk space usage.
                'SELECT DISTINCT ASP_NUMBER, UNIT_NUMBER, UNIT_TYPE, UNIT_STORAGE_CAPACITY, '
                'UNIT_SPACE_AVAILABLE, PERCENT_USED FROM QSYS2.SYSDISKSTAT'
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'asp_number', 'type': 'tag'},
            {'name': 'unit_number', 'type': 'tag'},
            {'name': 'unit_type', 'type': 'tag'},
            {'name': 'ibm_i.asp.unit_storage_capacity', 'type': 'gauge'},
            {'name': 'ibm_i.asp.unit_space_available', 'type': 'gauge'},
            {'name': 'ibm_i.asp.percent_used', 'type': 'gauge'},
        ],
    }


def get_base_disk_usage_73(timeout):
    return {
        'name': 'base_disk_usage_73',
        'query': {
            'text': (
                # Use DISTINCT because one serial number can have multiple lines with different RESOURCE NAMEs,
                # but we only want one metric per disk for disk space usage.
                'SELECT DISTINCT ASP_NUMBER, UNIT_NUMBER, UNIT_TYPE, SERIAL_NUMBER, UNIT_STORAGE_CAPACITY, '
                'UNIT_SPACE_AVAILABLE, PERCENT_USED FROM QSYS2.SYSDISKSTAT'
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'asp_number', 'type': 'tag'},
            {'name': 'unit_number', 'type': 'tag'},
            {'name': 'unit_type', 'type': 'tag'},
            {'name': 'serial_number', 'type': "tag"},
            {'name': 'ibm_i.asp.unit_storage_capacity', 'type': 'gauge'},
            {'name': 'ibm_i.asp.unit_space_available', 'type': 'gauge'},
            {'name': 'ibm_i.asp.percent_used', 'type': 'gauge'},
        ],
    }


def get_disk_usage(timeout):
    return {
        'name': 'disk_usage',
        'query': {
            'text': (
                # For IO / busy metrics, tag per connection as each connection as its own metrics
                "SELECT A.ASP_NUMBER, A.UNIT_NUMBER, A.UNIT_TYPE, A.SERIAL_NUMBER, A.RESOURCE_NAME, "
                "A.ELAPSED_PERCENT_BUSY, A.ELAPSED_IO_REQUESTS "
                # Two queries: one to fetch the stats, another to reset them
                "FROM TABLE(QSYS2.SYSDISKSTAT('NO')) A INNER JOIN TABLE(QSYS2.SYSDISKSTAT('YES')) B "
                "ON A.ASP_NUMBER = B.ASP_NUMBER AND A.UNIT_NUMBER = B.UNIT_NUMBER AND A.RESOURCE_NAME = B.RESOURCE_NAME"
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'asp_number', 'type': 'tag'},
            {'name': 'unit_number', 'type': 'tag'},
            {'name': 'unit_type', 'type': 'tag'},
            {'name': 'serial_number', 'type': "tag"},
            {'name': 'resource_name', 'type': "tag"},
            {'name': 'ibm_i.asp.percent_busy', 'type': 'gauge'},
            {'name': 'ibm_i.asp.io_requests_per_s', 'type': 'gauge'},
        ],
    }


def get_cpu_usage(timeout):
    return {
        'name': 'cpu_usage',
        'query': {
            'text': 'SELECT AVERAGE_CPU_UTILIZATION FROM QSYS2.SYSTEM_STATUS_INFO',
            'timeout': timeout,
        },
        'columns': [
            {'name': 'ibm_i.system.cpu_usage', 'type': 'gauge'},
        ],
    }


def get_jobq_job_status(timeout):
    return {
        'name': 'jobq_job_status',
        'query': {
            'text': (
                # TODO: try to move the JOB_NAME split logic to Python
                "SELECT SUBSTR(JOB_NAME,1,POSSTR(JOB_NAME,'/')-1) AS JOB_ID, "
                "SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1,POSSTR(SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1),'/')-1) AS JOB_USER, "  # noqa:E501
                "SUBSTR(SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1),POSSTR(SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1),'/')+1) AS JOB_NAME, "  # noqa:E501
                "JOB_SUBSYSTEM, 'JOBQ', JOB_QUEUE_LIBRARY, JOB_QUEUE_NAME, JOB_QUEUE_STATUS, 1 "
                "FROM TABLE(QSYS2.JOB_INFO('*JOBQ', '*ALL', '*ALL', '*ALL', '*ALL'))"
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'job_id', 'type': 'tag'},
            {'name': 'job_user', 'type': 'tag'},
            {'name': 'job_name', 'type': 'tag'},
            {'name': 'subsystem_name', 'type': 'tag'},
            {'name': 'job_status', 'type': 'tag'},
            {'name': 'job_queue_library', 'type': 'tag'},
            {'name': 'job_queue_name', 'type': 'tag'},
            {'name': 'job_queue_status', 'type': 'tag'},
            {'name': 'ibm_i.job.status', 'type': 'gauge'},
        ],
    }


def get_active_job_status(timeout):
    return {
        'name': 'active_job_status',
        'query': {
            'text': (
                # We prefer using ELAPSED_CPU_TIME / ELAPSED_TIME over ELAPSED_CPU_PERCENTAGE
                # because the latter only has a precision of one decimal.
                # ELAPSED_CPU_TIME is in milliseconds, while ELAPSED_TIME is in seconds
                # -> / 1000 to convert into seconds / seconds
                # -> * 100 to convert the resulting rate into a percentage
                # TODO: figure out why there a x4 difference with the value
                # given by ELAPSED_CPU_PERCENTAGE.
                # TODO: try to move the JOB_NAME split logic to Python
                "SELECT SUBSTR(A.JOB_NAME,1,POSSTR(A.JOB_NAME,'/')-1) AS JOB_ID, "
                "SUBSTR(A.JOB_NAME,POSSTR(A.JOB_NAME,'/')+1,POSSTR(SUBSTR(A.JOB_NAME,POSSTR(A.JOB_NAME,'/')+1),'/')-1) AS JOB_USER, "  # noqa:E501
                "SUBSTR(SUBSTR(A.JOB_NAME,POSSTR(A.JOB_NAME,'/')+1),POSSTR(SUBSTR(A.JOB_NAME,POSSTR(A.JOB_NAME,'/')+1),'/')+1) AS JOB_NAME, "  # noqa:E501
                "A.SUBSYSTEM, 'ACTIVE', A.JOB_STATUS, 1, "
                "CASE WHEN A.ELAPSED_TIME = 0 THEN 0 ELSE A.ELAPSED_CPU_TIME / (10 * A.ELAPSED_TIME) END AS CPU_RATE "
                # Two queries: one to fetch the stats, another to reset them
                "FROM TABLE(QSYS2.ACTIVE_JOB_INFO('NO', '', '', '')) A INNER JOIN TABLE(QSYS2.ACTIVE_JOB_INFO('YES', '', '', '')) B "  # noqa:E501
                # Assumes that INTERNAL_JOB_ID is unique, which should be the case
                "ON A.INTERNAL_JOB_ID = B.INTERNAL_JOB_ID"
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'job_id', 'type': 'tag'},
            {'name': 'job_user', 'type': 'tag'},
            {'name': 'job_name', 'type': 'tag'},
            {'name': 'subsystem_name', 'type': 'tag'},
            {'name': 'job_status', 'type': 'tag'},
            {'name': 'job_active_status', 'type': 'tag'},
            {'name': 'ibm_i.job.status', 'type': 'gauge'},
            {'name': 'ibm_i.job.cpu_usage', 'type': 'gauge'},
        ],
    }


def get_job_memory_usage(timeout):
    return {
        'name': 'job_memory_usage',
        'query': {
            'text': (
                # TODO: try to move the JOB_NAME split logic to Python
                "SELECT SUBSTR(JOB_NAME,1,POSSTR(JOB_NAME,'/')-1) AS JOB_ID, "
                "SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1,POSSTR(SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1),'/')-1) AS JOB_USER, "  # noqa:E501
                "SUBSTR(SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1),POSSTR(SUBSTR(JOB_NAME,POSSTR(JOB_NAME,'/')+1),'/')+1) AS JOB_NAME, "  # noqa:E501
                "SUBSYSTEM, JOB_STATUS, MEMORY_POOL, TEMPORARY_STORAGE FROM "
                "TABLE(QSYS2.ACTIVE_JOB_INFO('NO', '', '', ''))"
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'job_id', 'type': 'tag'},
            {'name': 'job_user', 'type': 'tag'},
            {'name': 'job_name', 'type': 'tag'},
            {'name': 'subsystem_name', 'type': 'tag'},
            {'name': 'job_active_status', 'type': 'tag'},
            {'name': 'memory_pool_name', 'type': 'tag'},
            {'name': 'ibm_i.job.temp_storage', 'type': 'gauge'},
        ],
    }


def get_memory_info(timeout):
    return {
        'name': 'memory_info',
        'query': {
            'text': (
                'SELECT POOL_NAME, SUBSYSTEM_NAME, CURRENT_SIZE, RESERVED_SIZE, DEFINED_SIZE FROM QSYS2.MEMORY_POOL_INFO'  # noqa:E501
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'pool_name', 'type': 'tag'},
            {'name': 'subsystem_name', 'type': 'tag'},
            {'name': 'ibm_i.pool.size', 'type': 'gauge'},
            {'name': 'ibm_i.pool.reserved_size', 'type': 'gauge'},
            {'name': 'ibm_i.pool.defined_size', 'type': 'gauge'},
        ],
    }


def get_subsystem_info(timeout):
    return {
        'name': 'subsystem',
        'query': {
            'text': (
                'SELECT SUBSYSTEM_DESCRIPTION, CASE WHEN STATUS = \'ACTIVE\' THEN '
                '1 ELSE 0 END, CURRENT_ACTIVE_JOBS FROM QSYS2.SUBSYSTEM_INFO'
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'subsystem_name', 'type': 'tag'},
            {'name': 'ibm_i.subsystem.active', 'type': 'gauge'},
            {'name': 'ibm_i.subsystem.active_jobs', 'type': 'gauge'},
        ],
    }


def get_job_queue_info(timeout):
    return {
        'name': 'job_queue',
        'query': {
            'text': (
                'SELECT JOB_QUEUE_NAME, JOB_QUEUE_STATUS, SUBSYSTEM_NAME,'
                'NUMBER_OF_JOBS, RELEASED_JOBS, SCHEDULED_JOBS, HELD_JOBS '
                'FROM QSYS2.JOB_QUEUE_INFO'
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'job_queue_name', 'type': 'tag'},
            {'name': 'job_queue_status', 'type': 'tag'},
            {'name': 'subsystem_name', 'type': 'tag'},
            {'name': 'ibm_i.job_queue.size', 'type': 'gauge'},
            {'name': 'ibm_i.job_queue.released_size', 'type': 'gauge'},
            {'name': 'ibm_i.job_queue.scheduled_size', 'type': 'gauge'},
            {'name': 'ibm_i.job_queue.held_size', 'type': 'gauge'},
        ],
    }


def get_message_queue_info(timeout, sev):
    return {
        'name': 'message_queue_info',
        'query': {
            'text': (
                f'SELECT MESSAGE_QUEUE_NAME, MESSAGE_QUEUE_LIBRARY, COUNT(*), SUM(CASE WHEN SEVERITY >= {sev} THEN 1 ELSE 0 END) '  # noqa:E501
                'FROM QSYS2.MESSAGE_QUEUE_INFO GROUP BY MESSAGE_QUEUE_NAME, MESSAGE_QUEUE_LIBRARY'
            ),
            'timeout': timeout,
        },
        'columns': [
            {'name': 'message_queue_name', 'type': 'tag'},
            {'name': 'message_queue_library', 'type': 'tag'},
            {'name': 'ibm_i.message_queue.size', 'type': 'gauge'},
            {'name': 'ibm_i.message_queue.critical_size', 'type': 'gauge'},
        ],
    }


def get_ibm_mq_info(timeout):
    return {
        'name': 'ibm_mq_info',
        'query': {
            'text': 'SELECT QNAME, COUNT(*) FROM TABLE(MQREADALL()) GROUP BY QNAME',
            'timeout': timeout,
        },
        'columns': [
            {'name': 'message_queue_name', 'type': 'tag'},
            {'name': 'ibm_i.ibm_mq.size', 'type': 'gauge'},
        ],
    }
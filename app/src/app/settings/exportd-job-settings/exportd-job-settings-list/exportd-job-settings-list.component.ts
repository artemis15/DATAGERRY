/*
* DATAGERRY - OpenSource Enterprise CMDB
* Copyright (C) 2019 - 2021 NETHINKS GmbH
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU Affero General Public License as
* published by the Free Software Foundation, either version 3 of the
* License, or (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU Affero General Public License for more details.

* You should have received a copy of the GNU Affero General Public License
* along with this program. If not, see <https://www.gnu.org/licenses/>.
*/


import { Component, OnDestroy, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { ReplaySubject } from 'rxjs';
import { ExportdJobService } from '../../services/exportd-job.service';
import { ExportdJob } from '../../models/exportd-job';
import { Router } from '@angular/router';
import { ToastService } from '../../../layout/toast/toast.service';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ExecuteState, ExportdType } from '../../models/modes_job.enum';
import { GeneralModalComponent } from '../../../layout/helpers/modals/general-modal/general-modal.component';
import { APIGetMultiResponse } from '../../../services/models/api-response';
import { takeUntil } from 'rxjs/operators';
import { CollectionParameters } from '../../../services/models/api-parameter';
import { Column, Sort, SortDirection } from '../../../layout/table/table.types';
import { PermissionService } from '../../../auth/services/permission.service';

@Component({
  selector: 'cmdb-task-settings-list',
  templateUrl: './exportd-job-settings-list.component.html',
  styleUrls: ['./exportd-job-settings-list.component.scss']
})
export class ExportdJobSettingsListComponent implements OnInit, OnDestroy {

  /**
   * Component un-subscriber.
   * @private
   */
  private subscriber: ReplaySubject<void> = new ReplaySubject<void>();

  /**
   * Table Template: active column.
   */
  @ViewChild('activeTemplate', { static: true }) activeTemplate: TemplateRef<any>;

  /**
   * Table Template: type column.
   */
  @ViewChild('typeTemplate', { static: true }) typeTemplate: TemplateRef<any>;

  /**
   * Table Template: destination column.
   */
  @ViewChild('destinationTemplate', { static: true }) destinationTemplate: TemplateRef<any>;

  /**
   * Table Template: running column.
   */
  @ViewChild('runningTemplate', { static: true }) runningTemplate: TemplateRef<any>;

  /**
   * Table Template: execution column.
   */
  @ViewChild('executionDateTemplate', { static: true }) executionDateTemplate: TemplateRef<any>;

  /**
   * Table Template: user column.
   */
  @ViewChild('userTemplate', { static: true }) userTemplate: TemplateRef<any>;


  /**
   * Table Template: job run column.
   */
  @ViewChild('jobRunTemplate', { static: true }) jobRunTemplate: TemplateRef<any>;

  /**
   * Table Template: job run state column.
   */
  @ViewChild('jobRunStateTemplate', { static: true }) jobRunStateTemplate: TemplateRef<any>;

  /**
   * Table Template: log state column.
   */
  @ViewChild('logTemplate', { static: true }) logTemplate: TemplateRef<any>;

  /**
   * Table Template: action column.
   */
  @ViewChild('actionTemplate', { static: true }) actionTemplate: TemplateRef<any>;

  /**
   * Table Buttons: add button.
   */
  @ViewChild('addButton', { static: true }) addButton: TemplateRef<any>;


  /**
   * Table columns definition.
   */
  public columns: Array<Column> = [];

  public tasks: Array<ExportdJob> = [];
  public tasksAPIResponse: APIGetMultiResponse<ExportdJob>;
  public totalTasks: number = 0;

  /**
   * Begin with first page.
   */
  public readonly initPage: number = 1;
  public page: number = this.initPage;

  /**
   * Max number of types per site.
   * @private
   */
  private readonly initLimit: number = 10;
  public limit: number = this.initLimit;

  /**
   * Filter query from the table search input.
   */
  public filter: string;

  /**
   * Default sort filter.
   */
  public sort: Sort = { name: 'public_id', order: SortDirection.DESCENDING } as Sort;

  /**
   * Loading indicator.
   */
  public loading: boolean = false;

  public modes = ExecuteState;
  public typeMode = ExportdType;
  private modalRef: NgbModalRef;

  public messageBlock: string = 'Exportd is an interface for exporting objects to external systems like monitoring systems,\n' +
    'ticket systems, backup software or any kind of other system. Exports are organized in Jobs. A Job contains Sources,\n' +
    'Destinations and Variables. Export Jobs can be triggered manually (by clicking on a button in the webui) or event based,\n' +
    'if the configured sources of a job were changed (e.g. a new object was added). Export Jobs can be of type Push (default)\n' +
    ' or Pull. Push Jobs are a push to an external system, which runs in a background process, while a Pull job is triggered\n' +
    ' by an external system via REST. The client directly gets the result within that REST call.';

  constructor(private taskService: ExportdJobService, private router: Router,
              private toast: ToastService, private modalService: NgbModal, private permissionService: PermissionService) {
  }

  public ngOnInit(): void {
    this.columns = [
      {
        display: 'Active',
        name: 'active',
        data: 'active',
        searchable: false,
        sortable: true,
        template: this.activeTemplate,
        cssClasses: ['text-center'],
        style: { width: '6rem' }
      },
      {
        display: 'Public ID',
        name: 'public_id',
        data: 'public_id',
        searchable: true,
        sortable: true
      },
      {
        display: 'Type',
        name: 'exportd_type',
        data: 'exportd_type',
        searchable: false,
        sortable: true,
        template: this.typeTemplate,
      },
      {
        display: 'Name',
        name: 'label',
        data: 'label',
        searchable: true,
        sortable: true
      },
      {
        display: 'External Systems',
        name: 'destination',
        data: 'destination',
        template: this.destinationTemplate,
        searchable: false,
        sortable: true
      },
      {
        display: 'Author',
        name: 'author_id',
        data: 'author_id',
        searchable: true,
        sortable: true,
        template: this.userTemplate
      },
      {
        display: 'Running',
        name: 'state',
        data: 'state',
        template: this.runningTemplate,
        searchable: false,
        sortable: true
      },
      {
        display: 'Last Execute Date',
        name: 'last_execute_date',
        data: 'last_execute_date',
        template: this.executionDateTemplate,
        searchable: false,
        sortable: true
      },
      {
        display: 'Execute State',
        name: 'state',
        data: 'state',
        template: this.jobRunStateTemplate,
        searchable: false,
        sortable: true
      }
    ] as Array<Column>;
    const jobRunRight = 'base.exportd.job.run';
    if (this.permissionService.hasRight(jobRunRight) || this.permissionService.hasExtendedRight(jobRunRight)) {
      this.columns.push({
        display: 'Execute Job',
        name: 'exportd_type',
        data: 'exportd_type',
        searchable: false,
        sortable: false,
        template: this.jobRunTemplate,
      } as Column);
    }
    const editRight = 'base.exportd.job.edit';
    if (this.permissionService.hasRight(editRight) || this.permissionService.hasExtendedRight(editRight)) {
      this.columns.push({
        display: 'Logs',
        name: 'public_id',
        data: 'public_id',
        searchable: false,
        sortable: false,
        template: this.logTemplate,
      } as Column);
    }
    const logRight = 'base.exportd.log.view';
    if (this.permissionService.hasRight(logRight) || this.permissionService.hasExtendedRight(logRight)) {
      this.columns.push({
        display: 'Actions',
        name: 'actions',
        data: 'public_id',
        searchable: false,
        sortable: false,
        fixed: true,
        template: this.actionTemplate,
        cssClasses: ['text-center'],
        cellClasses: ['actions-buttons']
      } as Column);
    }
    this.loadsTasksFromAPI();
  }

  private loadsTasksFromAPI() {
    this.loading = true;
    let query;
    if (this.filter) {
      query = [];
      const or = [];
      const searchableColumns = this.columns.filter(c => c.searchable);
      // Searchable Columns
      for (const column of searchableColumns) {
        const regex: any = {};
        regex[column.name] = {
          $regex: String(this.filter),
          $options: 'ismx'
        };
        or.push(regex);
      }
      query.push({
        $addFields: {
          public_id: { $toString: '$public_id' }
        }
      });
      or.push({
        public_id: {
          $elemMatch: {
            value: {
              $regex: String(this.filter),
              $options: 'ismx'
            }
          }
        }
      });
      query.push({ $match: { $or: or } });
    }
    const params: CollectionParameters = {
      filter: query, limit: this.limit,
      sort: this.sort.name, order: this.sort.order, page: this.page
    };
    this.taskService.getTasks(params).pipe(takeUntil(this.subscriber)).subscribe((apiResponse: APIGetMultiResponse<ExportdJob>) => {
      this.tasksAPIResponse = apiResponse;
      this.tasks = apiResponse.results as Array<ExportdJob>;
      this.totalTasks = apiResponse.total;
      this.loading = false;
    });
  }

  public run_job_manual(job: ExportdJob) {
    job.running = true;
    job.state = ExecuteState.RUNNING;
    this.taskService.putTask(job).pipe(takeUntil(this.subscriber)).subscribe(value => this.toast.success('Job started'),
      error => this.toast.error(error),
      () =>
        this.taskService.run_task(job.public_id).pipe(takeUntil(this.subscriber)).subscribe(resp => console.log(resp),
          error => {
          },
          () => this.loadsTasksFromAPI())
    );
  }

  /**
   * On table sort change.
   * Reload all tasks.
   *
   * @param sort
   */
  public onSortChange(sort: Sort): void {
    this.sort = sort;
    this.loadsTasksFromAPI();
  }


  /**
   * On table page change.
   * Reload all tasks.
   *
   * @param page
   */
  public onPageChange(page: number) {
    this.page = page;
    this.loadsTasksFromAPI();
  }

  /**
   * On table page size change.
   * Reload all tasks.
   *
   * @param limit
   */
  public onPageSizeChange(limit: number): void {
    this.limit = limit;
    this.page = this.initPage;
    this.loadsTasksFromAPI();
  }

  /**
   * On table search change.
   * Reload all tasks.
   *
   * @param search
   */
  public onSearchChange(search: any): void {
    this.page = this.initPage;
    if (search) {
      this.filter = search;
    } else {
      this.filter = undefined;
    }
    this.loadsTasksFromAPI();
  }

  public delTask(itemID: number) {

    this.modalRef = this.modalService.open(GeneralModalComponent);
    this.modalRef.componentInstance.title = 'Delete Exportd Job';
    this.modalRef.componentInstance.modalMessage = 'Are you sure you want to delete this Exportd Job?';
    this.modalRef.componentInstance.buttonDeny = 'Cancel';
    this.modalRef.componentInstance.buttonAccept = 'Delete';
    this.modalRef.result.then((result) => {
      if (result) {
        this.taskService.deleteTask(itemID).pipe(takeUntil(this.subscriber)).subscribe(resp => this.toast.success('Task deleted!'),
          error => this.toast.error(`Error while deleting task: ${ error }`),
          () => this.loadsTasksFromAPI());
      }
    });
  }

  public ngOnDestroy(): void {
    this.subscriber.next();
    this.subscriber.complete();
    if (this.modalRef) {
      this.modalRef.close();
    }
  }

  public showAlert(): void {
    $('#infobox').show();
  }

}

/*
* DATAGERRY - OpenSource Enterprise CMDB
* Copyright (C) 2019 NETHINKS GmbH
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
* along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

import { Component, OnInit } from '@angular/core';
import { FileElement } from '../../model/file-element';
import { FileMetadata } from '../../model/metadata';
import { FileService } from '../../service/file.service';

@Component({
  selector: 'cmdb-file-view-list',
  templateUrl: './file-view-list.component.html',
  styleUrls: ['./file-view-list.component.scss']
})
export class FileViewListComponent implements OnInit {

  public files: FileElement[];
  private metadata: FileMetadata = new FileMetadata();

  constructor(private fileService: FileService) { }

  ngOnInit() {
    this.fileService.getAllFilesList(this.metadata).subscribe((data: any) => {
      this.files = data;
    });
  }

}